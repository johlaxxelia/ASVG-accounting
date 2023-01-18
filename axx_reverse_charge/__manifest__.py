{
    'name': 'Axx Reverse Charge',
    'summary': 'Axx Reverse Charge',
    'description': 'To manage the tax based on the product (article) category',
    'category': 'Accounting',
    'version': '16.0.1.0.0',
    'author': 'axxelia GmbH',
    'website': 'http://www.axxelia.com',
    'depends': [
        # ---------------------
        # Odoo
        # ---------------------
        'sale_management',
        'purchase'
        # ---------------------
        # OCA
        # ---------------------
        # ---------------------
        # EE
        # ---------------------
        # ---------------------
        # Thirdparty
        # ---------------------
        # ---------------------
        # Axxelia
        # ---------------------
        # ---------------------
        # PROJECT
        # ---------------------

    ],
    'data': [
        # Security
        # Wizards
        # Data
        # views
        'views/product/product_category_views.xml',
        'views/sale/sale_order_views.xml',
        'views/purchase/purchase_order_views.xml',
        # Menus
        # Reports
        # Templates
    ],
    'installable': True,
    'application': True
}
