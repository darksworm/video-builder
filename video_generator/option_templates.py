from typing import Dict, List


def get_template_options_for_template_name(template_name: str, templates: Dict[str, str]) -> List[str]:
    option_text = templates[template_name]
    split_options = option_text.splitlines(keepends=False)
    return split_options


def replace_template_option_names_with_template_options(option_list: List[str], templates: Dict[str, str]) -> List[str]:
    replaced = []
    for name in option_list:
        options = get_option_or_template_options_list(name, templates)
        replaced = [*replaced, *options]
    return replaced


def get_option_or_template_options_list(option: str, templates: Dict[str, str]) -> List[str]:
    if option in templates:
        preset_options = get_template_options_for_template_name(option, templates)
        return preset_options
    else:
        return [option]
