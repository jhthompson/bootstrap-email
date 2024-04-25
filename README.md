# bootstrap-email

Python port of [bootstrap-email](https://github.com/bootstrap-email/bootstrap-email)


## TODOs

- the Ruby premailer expanders border shorthand like "border: 0" to "border-width: 0" https://github.com/premailer/css_parser/blob/deaae98275d71422fc8bc2d1ca1148f6ce982e5c/lib/css_parser/rule_set.rb#L334
  - the Python premailer DOES NOT do this... can we work around in this lib? Add patch to Python premailer?
- the Ruby premailer also turns some attributes like "background-color" in to separate attributes (unless preserve_style_attribute is passed as True?) https://github.com/premailer/premailer/blob/62c2a84b24ef84832d00f6106d2dd884838b7564/lib/premailer/adapter/nokogiri_fast.rb#L88
  - the Python premailer currently does NOT do this
  - it SHOULD be doing this according to [this code](https://github.com/peterbe/premailer/blob/f4ded0b9701c4985e7ff5c5beda83324c264ea62/premailer/premailer.py#L620)