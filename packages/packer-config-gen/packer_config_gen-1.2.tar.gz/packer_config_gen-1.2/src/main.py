import os
import argparse
from loader import load_yaml, merge_configs, insert_env_vars
from render import render_template

def init_parse_arg() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Packer configs from YAML/Jinja2.")
    parser.add_argument("--os", type=str, required=True, help="Name of the OS config (e.g. ubuntu, centos)")
    return parser.parse_args()

def build_artifacts(templates_dir, context, build_dir, build_name) -> None:
    render_template(
        os.path.join(templates_dir),
        'hypervisor.pkr.hcl.j2', 
        context, 
        build_dir,
        f"{build_name}.pkr.hcl"
    )

    installer_name = context.get('installer')
    files_list = context.get('installer_files')

    if installer_name and files_list:        
        for item in files_list:            
            output_file_path = os.path.join(build_dir, installer_name)

            render_template(
                os.path.join(templates_dir, installer_name),
                f"{item}.j2",
                context,
                output_file_path,
                item
            )

def main() -> None:
    args = init_parse_arg()

    base_dir = os.getcwd()
    configs_dir = os.path.join(base_dir, 'configs')
    configs_os_dir = os.path.join(configs_dir, 'os')
    templates_dir = os.path.join(base_dir, 'templates')
    output_dir = os.path.join(base_dir, 'artifacts')

    hv_config_path = os.path.join(configs_dir, 'hypervisor.yaml')
    hv_data = load_yaml(hv_config_path)

    os_file_path = os.path.join(configs_os_dir, f'{args.os}.yaml')
    os_data = load_yaml(os_file_path)

    context = merge_configs(hv_data, os_data)
    insert_env_vars(context)

    build_name = args.os
    build_dir = os.path.join(output_dir, build_name)

    build_artifacts(templates_dir, context, build_dir, build_name)

if __name__ == "__main__":
    main()