def get_template_options(preset_name, templates):
    option_text = templates[preset_name]
    split_options = option_text.splitlines(keepends=False)
    return split_options

def insert_option_templates(option_list, templates):
    inserted = []
    for name in option_list:
        options = get_option_or_template_options_list(name, templates)
        inserted = [*inserted, *options]
    return inserted

def get_option_or_template_options_list(option, templates) -> list:
    if option in templates:
        preset_options = get_template_options(option, templates)
        return preset_options
    else:
        return [option]
