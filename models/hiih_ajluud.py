from odoo import models, fields, api
from odoo.exceptions import AccessError

class HiihAjluud(models.Model):
    _name = 'mandal.helpdesk.ajil'
    _description = 'Hiih Ajluud'

    name = fields.Char(string="Ажлын нэр", required=True)
    description = fields.Text(string="Тайлбар")
    assigned_user_id = fields.Many2one(
        'res.users',
        string="Оноосон ажилтан"
    )
    state = fields.Selection(
        [
            ('todo', 'Ноорог'),
            ('in_progress', 'Хүн авсан'),
            ('done', 'Хийж гүйцэтгэсэн'),
        ],
        string="Төлөв",
        default='todo'
    )

    # 🔐 Захирал эсэх
    def _is_boss(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )
        return bool(employee and employee.job_id.name == 'Boss')

    # ✅ Захирлын булангаас create зөвшөөрнө
    @api.model
    def create(self, vals):
        if not self._is_boss():
            raise AccessError("Та зөвхөн харах эрхтэй!")
        return super().create(vals)

    # ❌ Ажилтан write хийж болохгүй
    def write(self, vals):
        if not self._is_boss():
            raise AccessError("Та энэ ажлыг өөрчлөх эрхгүй!")
        return super().write(vals)

    # ❌ Устгах эрхгүй
    def unlink(self):
        if not self._is_boss():
            raise AccessError("Та устгах эрхгүй!")
        return super().unlink()

    # onchange хэвээр
    @api.onchange('assigned_user_id')
    def _onchange_assigned_user_id(self):
        if self.assigned_user_id:
            self.state = 'in_progress'

# ШИНЭ: Хүсэлттэй холбох
    huselt_id = fields.Many2one(
        'mandal.helpdesk.huselt',
        string="Хүсэлт",
        readonly=True
    )
    
    assigned_user_id = fields.Many2one(
        'res.users',
        string="Хариуцсан ажилтан"
    )
    
    deadline = fields.Date(string="Дуусах хугацаа")
    
    state = fields.Selection([
        ('draft', 'Төлөвлөгөө'),
        ('in_progress', 'Явагдаж байгаа'),
        ('done', 'Дууссан'),
        ('cancelled', 'Цуцалсан')
    ], string="Төлөв", default='draft')
    
    priority = fields.Selection([
        ('low', 'Бага'),
        ('medium', 'Дунд'),
        ('high', 'Өндөр')
    ], string="Чухал байдал", default='medium')
    
    # ШИНЭ: Хүсэлт явуулсан хүний мэдээлэл
    huselt_user_id = fields.Many2one(
        'res.users',
        string="Хүсэлт явуулсан",
        related='huselt_id.user_id',
        store=True
    )
    
    huselt_department_id = fields.Many2one(
        'hr.department',
        string="Хүсэлт явуулсан хэлтэс",
        related='huselt_id.department_id',
        store=True
    )