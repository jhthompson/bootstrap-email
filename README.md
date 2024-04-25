# bootstrap-email

Python port of [bootstrap-email](https://github.com/bootstrap-email/bootstrap-email)


## TODOs

- the Ruby premailer expanders border shorthand like "border: 0" to "border-width: 0" https://github.com/premailer/css_parser/blob/deaae98275d71422fc8bc2d1ca1148f6ce982e5c/lib/css_parser/rule_set.rb#L334
  - the Python premailer DOES NOT do this... can we work around in this lib? Add patch to Python premailer?