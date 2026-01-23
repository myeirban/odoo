from odoo import models, fields, api
from odoo.exceptions import AccessError

class AjilOnooh(models.Model):
    _name = "mandal.helpdesk.ooriinbolonbusad.heltesd.ajil.onooh"
    _description = "ajil onooh shuu zovhon heltsiin zahiral orno shuu"

    name = fields.Char(
        string="Тухайн хэлтэсийн тэр ажилтанд оноож өгсөн ажлууд",
        required=True
    )
    description = fields.Text(string="Ажлын тайлбар")
    assigned_user_id = fields.Many2one(
        'res.users',
        string="Оноосон ажилтан"
    )

    # 🔐 Захирал эсэхийг шалгах
    def _check_is_boss(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )
        if not employee or employee.job_id.name != 'Boss':
            raise AccessError("Зөвхөн Захирал энэ үйлдлийг хийх эрхтэй!")

    # ✅ Create – зөвхөн захирал
    @api.model
    def create(self, vals):
        self._check_is_boss()
        return super().create(vals)

    # ❌ Edit – ажилчид засах боломжгүй
    def write(self, vals):
        self._check_is_boss()
        return super().write(vals)

    # ❌ Delete – ажилчид устгах боломжгүй
    def unlink(self):
        self._check_is_boss()
        return super().unlink()
