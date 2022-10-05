import os

import h5py
import numpy as np
from tqdm import tqdm


def get_key(h5_name: str) -> int:
    return int(h5_name.split("-")[-1].split(".")[0])


def process_single_rms_field(
    input_path: str, output_path: str, verbose: bool = False
) -> None:
    h5_files = [p for p in os.listdir(input_path) if p.endswith(".h5")]
    h5_files = sorted(h5_files, key=get_key)

    with h5py.File(output_path, "x", libver="latest") as out:
        data_grp = out.create_group("data")
        for i, h5_file in enumerate(tqdm(h5_files, desc="h5 files", disable=verbose)):
            with h5py.File(
                os.path.join(input_path, h5_file), "r", libver="latest"
            ) as f:
                if verbose:
                    print(h5_file, end="...")
                solve_steps = np.sort(np.array([int(key) for key in f["data"]]))
                if i == 0:
                    f["solution/device"].copy("mesh", out)
                    # mesh_grp = out.create_group("mesh")
                    # for k, v in f["solution/device/mesh"].items():
                    #     mesh_grp[k] = np.asarray(v)
                    # for step in solve_steps:
                    #     f["data"].copy(str(step), data_grp)
                if False:
                    pass
                else:
                    step = solve_steps[-1]
                    print(step)
                    f["data"].copy(str(step), data_grp, name=str(step + i))
                    # grp = data_grp.create_group(str(step + i))
                    # for k, v in f[f"data/{step}"].attrs.items():
                    #     grp.attrs[k] = v
                    # for k, v in f[f"data/{step}"].items():
                    #     grp[k] = np.asarray(v)
                if verbose:
                    print("DONE")

    return output_path


def process_many_rms_fields(
    input_dir: str, output_dir: str, verbose: bool = False
) -> None:
    input_paths = []
    for p in os.listdir(input_dir):
        try:
            n = int(p)
            input_paths.append(n)
        except ValueError:
            pass
    input_paths = sorted(input_paths)
    os.makedirs(output_dir, exist_ok=False)
    for n in input_paths:
        input_path = os.path.join(input_dir, str(n))
        output_path = os.path.join(output_dir, str(n))
        if verbose:
            print(input_path)
        # output_path = os.path.join(output_dir, f"run-{n:02}.h5")
        process_single_rms_field(input_path, output_path, verbose=verbose)


def main():

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", type=str, help="Input directory.")
    parser.add_argument("-o", "--output", type=str, help="Output directory.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose.")

    args = parser.parse_args()

    process_many_rms_fields(args.input, args.output, verbose=args.verbose)


if __name__ == "__main__":
    main()