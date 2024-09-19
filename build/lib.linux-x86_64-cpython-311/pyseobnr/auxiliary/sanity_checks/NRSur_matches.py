import argparse
import importlib
import os
import sys

import gwsurrogate
import numpy as np
from bilby.core.utils import check_directory_exists_and_if_not_mkdir
from pathos.multiprocessing import ProcessingPool as Pool


from pyseobnr.auxiliary.sanity_checks.metrics  import UnfaithfulnessModeByModeLAL
from pyseobnr.auxiliary.external_models  import NRHybSur2dq15Model, NRHybSur3dq8Model,SEOBNRv4HM_LAL
from pyseobnr.generate_waveform import generate_modes_opt

from pyseobnr.auxiliary.sanity_checks.parameters import parameters_random_fast, parameters_random_2D_fast

# Reproducible
seed = 150914

mode_list_v5HM = [(2, 2), (2, 1), (3, 3), (3, 2), (4, 4), (4, 3), (5, 5)]
mode_list_v4HM = [(2, 2), (2, 1), (3, 3), (4, 4), (5, 5)]

sur_3dq8 = gwsurrogate.LoadSurrogate("NRHybSur3dq8")
sur_2dq15 = gwsurrogate.LoadSurrogate("NRHybSur2dq15")


def mismatch_NRHybSur(
    q: float,
    chi1: float,
    chi2: float,
    model_name: str,
    approximant_name: str,
    MR_only: bool = False,
):
    # sur = gwsurrogate.LoadSurrogate(model_name)
    if model_name == "NRHybSur2dq15":
        target_model = NRHybSur2dq15Model(
            q,
            chi1,
            chi2,
            0.015,
        )
        sur = sur_2dq15
        mode_list = mode_list_v4HM

    elif model_name == "NRHybSur3dq8":
        target_model = NRHybSur3dq8Model(
            q,
            chi1,
            chi2,
            0.015,
        )
        sur = sur_3dq8
        mode_list = mode_list_v5HM
    target_model(sur)

    if approximant_name == "SEOBNRv5HM":
        _,_,calib_model = generate_modes_opt(q,chi1,chi2,target_model.omega0,debug=True)


    elif approximant_name == "SEOBNRv4HM":
        calib_model = SEOBNRv4HM_LAL(
            target_model.q,
            target_model.chi_1,
            target_model.chi_2,
            target_model.omega0,
        )
        calib_model()
        mode_list = mode_list_v4HM


    masses = np.arange(10, 310, 10)
    unf_settings = {"debug": True, "masses": masses}
    unf = UnfaithfulnessModeByModeLAL(settings=unf_settings)



    mms = []
    for mode in mode_list:
        ell, m = mode
        mm = unf(target_model, calib_model, ell=ell, m=m)
        mms.append(mm)
    return (target_model.q, target_model.chi_1, target_model.chi_2, np.array(mms))


def process_one_case(input):
    q, chi1, chi2, model_name, approximant_name, MR_only = input
    q, chi1, chi2, mm = mismatch_NRHybSur(
        q, chi1, chi2, model_name, approximant_name, MR_only
    )
    # return np.array([q, chi1, chi2, *mm])
    return mm


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compute mismatch against NRSur")
    p.add_argument("--points", type=int, help="Number of points", default="5000")
    p.add_argument("--chi-max", type=float, help="Maximum spin", default="0.8")
    p.add_argument("--q-max", type=float, help="Maximum mass-ratio", default="8.0")
    p.add_argument(
        "--name", type=str, help="Name of the output file", default="mismatch"
    )
    p.add_argument(
        "--plots", action="store_true", help="Make diagnostic plots", default=True
    )
    p.add_argument(
        "--model-name",
        type=str,
        help="Name of the surrogate model",
        default="NRHybSur3dq8",
    )
    p.add_argument(
        "--approximant-name",
        type=str,
        help="Name of the approximant",
        default="SEOBNRv5HM",
    )
    p.add_argument(
        "--plots-only",
        action="store_true",
        help="Only generate plots, don't recompute things",
    )
    p.add_argument("--n-cpu", type=int, help="Number of cores to use", default=64)
    p.add_argument(
        "--include-all",
        action="store_true",
        help="Include odd m modes close to equal mass",
        default=False,
    )
    p.add_argument(
        "--mr-only",
        action="store_true",
        help="Compute unfaithfulness only over the merger-ringdown",
        default=False,
    )

    args = p.parse_args()

    if args.model_name == "NRHybSur2dq15":
        mode_list = mode_list_v4HM
    elif args.model_name == "NRHybSur3dq8":
        mode_list = mode_list_v5HM

    if args.approximant_name == "SEOBNRv4HM":
        mode_list = mode_list_v4HM

    if not args.plots_only:
        # sur = gwsurrogate.LoadSurrogate(args.model_name)

        if args.model_name == "NRHybSur2dq15":
            qarr, chi1arr = parameters_random_2D_fast(
                args.points,
                1.0,
                args.q_max,
                -args.chi_max,
                args.chi_max,
                random_state=seed,
            )
            lst = [
                (q, chi1, 0.0, args.model_name, args.approximant_name, args.mr_only)
                for q, chi1 in zip(qarr, chi1arr)
            ]
            # This model supports non-zero primary spin only
            chi2arr = np.zeros(args.points)

        elif args.model_name == "NRHybSur3dq8":
            qarr, chi1arr, chi2arr = parameters_random_fast(
                args.points,
                1.0,
                args.q_max,
                -args.chi_max,
                args.chi_max,
                -args.chi_max,
                args.chi_max,
                random_state=seed,
            )
            lst = [
                (q, chi1, chi2, args.model_name, args.approximant_name, args.mr_only)
                for q, chi1, chi2 in zip(qarr, chi1arr, chi2arr)
            ]


        pool = Pool(args.n_cpu)
        all_means = pool.map(process_one_case, lst)

        all_means = np.array(all_means)
        # This is an array with shape n cases x p modes x m masses
        mismatches = {}
        for mode in mode_list:
            mismatches[mode] = []
        for i in range(len(all_means)):
            mm_for_case = all_means[i]
            for j, mode in enumerate(mode_list):
                mode_mismatch = mm_for_case[j]
                mismatches[mode].append(mode_mismatch)

        for mode in mode_list:
            ell, m = mode
            np.savetxt(
                f"{args.name}_{args.model_name}_{args.approximant_name}{ell}{m}.dat",
                mismatches[mode],
            )

        np.savetxt(f"parameters_{args.model_name}.dat", np.c_[qarr, chi1arr, chi2arr])
    ### Plots ###

    if args.plots:

        import matplotlib
        import matplotlib.pyplot as plt

        plt_dir = "./plots"
        check_directory_exists_and_if_not_mkdir(plt_dir)

        res_path = args.name
        params = np.genfromtxt(f"parameters_{args.model_name}.dat")
        q = params[:, 0]
        chi1 = params[:, 1]
        chi2 = params[:, 2]

        nu = q / (1 + q) ** 2
        m1 = q / (1 + q)
        m2 = 1 / (1 + q)
        ap = m1 * chi1 + m2 * chi2
        am = m1 * chi1 - m2 * chi2
        for mode in mode_list:
            ell, m = mode
            mm_M = np.loadtxt(
                f"{args.name}_{args.model_name}_{args.approximant_name}{ell}{m}.dat"
            )
            if not args.include_all:
                if m % 2 == 1:
                    idx_notEMES = np.where((q > 1.01) | (np.abs(chi1 - chi2) > 0.01))[0]
                    q_pl = q[idx_notEMES]
                    ap_pl = ap[idx_notEMES]
                    mm_M = mm_M[idx_notEMES]
                else:
                    q_pl = q
                    ap_pl = ap
            else:
                q_pl = q
                ap_pl = ap

            if args.mr_only:
                # MR only mismatch uses flat noise curve, does not depend on M
                mm = mm_M
            else:
                M = np.arange(10, 310, 10)

                # maximum of mm_M across total mass for histogram
                mm = []
                for mp in mm_M:
                    mm.append(np.max(mp))
                mm = np.array(mm)

                # Spaghetti plot
                for mp in mm_M:
                    plt.plot(M, mp, color="C0", linewidth=0.5)
                plt.axhline(0.01, ls="--", color="red")
                plt.yscale("log")
                plt.xlabel("M")
                plt.ylabel("$\mathcal{M}$")
                plt.xlim(10, 300)
                plt.savefig(
                    f"{plt_dir}/mm_spaghetti_{args.model_name}_{args.approximant_name}{ell}{m}.png",
                    bbox_inches="tight",
                    dpi=300,
                )
                plt.close()

            # Histogram
            plt.hist(
                mm,
                bins=np.logspace(start=np.log10(0.00001), stop=np.log10(1.0), num=50),
                alpha=0.4,
                label=args.approximant_name + " - " + args.model_name,
            )
            plt.axvline(np.median(mm), c="C0", ls="--")
            plt.legend(loc="best")
            plt.gca().set_xscale("log")
            plt.xlabel("$\mathcal{M}_{\mathrm{Max}}$")
            plt.title(
                "$\mathcal{M}_{\mathrm{median}} = $" + f"{np.round(np.median(mm),6)}"
            )
            plt.savefig(
                f"{plt_dir}/mm_hist_{args.model_name}_{args.approximant_name}{ell}{m}.png",
                bbox_inches="tight",
                dpi=300,
            )
            plt.close()

            # CDF
            plt.hist(
                mm,
                bins=np.logspace(start=np.log10(0.00001), stop=np.log10(1.0), num=100),
                alpha=0.4,
                label=args.approximant_name + " - " + args.model_name,
                cumulative=True,
                density=True,
                histtype="step",
                lw=2,
            )
            plt.legend(loc="best")
            plt.gca().set_xscale("log")
            plt.xlabel("$\mathcal{M}_{\mathrm{Max}}$")
            plt.title(
                "$\mathcal{M}_{\mathrm{median}} = $" + f"{np.round(np.median(mm),6)}"
            )
            plt.grid(True, which="both", ls=":")
            plt.savefig(
                f"{plt_dir}/mm_cdf_{args.model_name}_{args.approximant_name}{ell}{m}.png",
                bbox_inches="tight",
                dpi=300,
            )

            plt.close()

            # Mismatch across parameter space
            mm_s, q_s, ap_s = map(list, zip(*sorted(zip(mm, q_pl, ap_pl))))
            plt.scatter(
                q_s, ap_s, c=mm_s, linewidths=1, norm=matplotlib.colors.LogNorm()
            )
            plt.ylabel("$\chi_{\mathrm{eff}}$")
            plt.xlabel("$q$")
            cbar = plt.colorbar()
            cbar.set_label("$\mathcal{M}$")
            plt.savefig(
                f"{plt_dir}/mm_scatter_{args.model_name}_{args.approximant_name}{ell}{m}.png",
                bbox_inches="tight",
                dpi=300,
            )
            plt.close()
