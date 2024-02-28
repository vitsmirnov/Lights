def main() -> None:
    source_file = "settings.txt"
    out_file = "settings_instance.py"
    convert_settings_txt_to_py(source_file, out_file)
    print(f"Converting from \"{source_file}\" to \"{out_file}\" is complete.")


def convert_settings_txt_to_py(in_file_name: str, out_file_name: str) -> bool:
    data = None
    try:
        with open(in_file_name, "r") as f:
            data = f.readlines()
    except:
        print(f"Can't open or read file \"{in_file_name}\".")
        return False
    
    try:
        with open(out_file_name, "w") as f:
            f.write("SETTINGS_INSTANCE = (\n")
            for line in data:
                f.write(f"    \"{line.replace("\\", "\\\\").rstrip()}\\n\"\n")  # add ","?
            f.write(")\n")
    except:
        print(f"Can't write to file \"{out_file_name}\".")
        return False
    
    return True


def save_lines_to_file(file_name: str, lines: tuple[str] | list[str]) -> bool:
    try:
        with open(file_name, "w") as f:
            f.writelines(lines)
    except:
        print(f"Can't write to file \"{file_name}\".")
        return False
    return True



if __name__ == "__main__":
    main()