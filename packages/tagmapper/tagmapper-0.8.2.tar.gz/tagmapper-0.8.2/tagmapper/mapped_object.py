class Mapped_Object:
    def __str__(self):
        s = f"{self.inst_code} - {self.object_name}"
        for att in self.attribute:
            s = f"{s}\n{str(att)}"

        return s
