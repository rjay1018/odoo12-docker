from odoo import models
from num2words import num2words

class AmountToWordsPH(models.AbstractModel):
    _name = "amount.to.words.ph"
    _description = "Convert Amount to Words (Philippine Peso Format)"

    @staticmethod
    def to_words(amount):
        amount = float(amount)

        pesos = int(amount)
        centavos = int(round((amount - pesos) * 100))

        words = num2words(pesos, lang='en').replace('-', ' ').title()
        words = words.replace(" And ", " ")

        if centavos == 0:
            return f"{words} Pesos Only"
        return f"{words} Pesos and {centavos:02d}/100"
