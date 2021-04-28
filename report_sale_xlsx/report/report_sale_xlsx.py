import datetime
from odoo import fields, models, _


class ReportSaleXlsx(models.AbstractModel):
    """
    Set up Excel Report based on module report_xlsx to inherit feature generate_xlsx_report
    """
    _name = 'report.report_sale_order_xlsx.report_sale_xlsx'
    _description = 'Structure Excel Report Sale'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        """
        set up excel report
        :param workbook:
        :param data:
        :param objects:
        :return:
        """
        workbook.set_properties({'comments': 'Created with Python and XlsxWriter'})
        sheet = workbook.add_worksheet(_("Sale"))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(80)
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 40)
        bold = workbook.add_format({'bold': True})
        title_style = workbook.add_format({
            'bold': True, 'bg_color': '#FFFFCC', 'bottom': 1
        })
        sheet_title = [
            _('Order Reference'),
            _('Order Date'),
            _('Customer'),
            _('Sales Person'),
            _('Products'),
            _('Quantity'),
            _('Total'),
            _('Total Untaxed')
        ]
        sheet.set_row(0, None, None, {'collapsed': 1})
        sheet.write_row(1, 0, sheet_title, title_style)
        sheet.freeze_panes(2, 0)
        row = 2
        col = 0
        for o in objects:
            sheet.write(row, col, o.name)
            date = fields.Datetime.to_string(o.date_order)
            sheet.write(row, col + 1, date)
            sheet.write(row, col + 2, o.partner_id.name)
            sheet.write(row, col + 3, o.user_id.name)
            sheet.write(row, col + 6, o.amount_total)
            sheet.write(row, col + 7, o.amount_untaxed)
            for line in o.order_line:
                sheet.write(row, col + 4, line.product_id.name, bold)
                sheet.write(row, col + 5, line.product_uom_qty)
                row += 1

