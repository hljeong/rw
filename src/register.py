class field:
    def __init__(self, name, msb, lsb=None, a="rw", r=0):
        self.name = name
        self.msb = msb
        self.lsb = lsb or msb
        self.access = a
        self.reset = r

        self.bitwidth = self.msb - self.lsb + 1
        self.offset = self.lsb

        assert self.offset >= 0 and self.bitwidth >= 1

    def extract(self, value):
        return (value >> self.offset) & ((1 << self.bitwidth) - 1)

    def apply(self, value):
        assert 0 <= value and value < (1 << self.bitwidth)
        return value << self.offset

    def __xor__(self, other):
        return other.msb < self.lsb or self.msb < other.lsb


def register(name, *fields, w=32):
    fields = sorted(fields, key=lambda field: field.offset)
    for field in fields:
        assert field.msb < w
    for field0, field1 in zip(fields, fields[1:]):
        assert field0 ^ field1

    max_field_name_len = max(len(field.name) for field in fields)
    max_msb_len = max(len(str(field.msb)) for field in fields)

    attrs = {}

    def attr(func):
        attrs[func.__name__] = func
        return func

    @attr
    def __init__(self, rw):
        self.read = rw.read
        self.write = rw.write

    @attr
    def what(value):
        return {field.name: field.extract(value) for field in fields}

    @attr
    def where(**field_values):
        return sum(
            field.apply(
                field_values[field.name] if field.name in field_values else field.reset
            )
            for field in fields
        )

    @attr
    def decode(self):
        return what(self.read())

    @attr
    def modify(self, **field_values):
        self.write(where(**dict(self.decode(), **field_values)))

    @attr
    def overwrite(self, **field_values):
        self.write(where(**field_values))

    @attr
    def show(self):
        value = self.read()
        field_values = what(value)
        max_field_value_len = max(
            len(str(field_value)) for field_value in field_values.values()
        )
        print(f"{value} (0x{value:0{(w + 3) // 4}x})")
        for field in fields:
            print(
                " ".join(
                    [
                        f"[{field.msb:>{max_msb_len}}:{field.lsb:>{max_msb_len}}]",
                        f"{field.name:<{max_field_name_len}}",
                        "=",
                        f"{field_values[field.name]:<{max_field_value_len}}",
                        f"(0x{field_values[field.name]:0{(field.bitwidth + 3) // 4}x})",
                    ]
                )
            )

    return type(name, (), attrs)


f = field
r = register
