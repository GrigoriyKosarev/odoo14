{
    'name': 'GK TEST',
    'version': '15.0.0.0.1',
    'summary': """
        BOM.
    """,
    'category': 'Customizations',
    'author': 'grigoriykosarev@gmail.com',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['mrp', 'base', 'stock', 'sale', 'purchase'],
    'external_dependencies': {'python': [], },
    'data': [
        'security/ir.model.access.csv',
        'wizard/test_wizard_views.xml',
        'wizard/test_sale_order_line_wizard.xml',
        'wizard/stock_forecast_wizard_views.xml',
        'report/product_reports_label.xml',
        'report/report_gk_test.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'support': 'grigoriykosarev@gmail.com',
}
