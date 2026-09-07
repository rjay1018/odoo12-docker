{
    "name"          : "Generic Excel Report",
    "version"       : "1.0",
    "author"        : "Miftahussalam",
    "website"       : "https://blog.miftahussalam.com",
    "category"      : "Reporting",
    "license"       : "OPL-1",
    "support"       : "me@miftahussalam.com",
    "summary"       : "Create excel report with dynamic and simple query",
    "price"         : "40",
    "currency"      : "USD",
    "description"   : """
        
    """,
    "depends"       : [
        "base",
        "product",
        # "purchase",
    ],
    "data"          : [
        "views/ms_generic_excel_report_views.xml",
        "wizard/ms_generic_excel_report_wizard.xml",
        # "data/ms_generic_excel_report.xml",
        "security/ir.model.access.csv",
    ],
    "demo"          : [],
    "test"          : [],
    "images"        : [
        "static/description/images/main_screenshot.png",
    ],
    "qweb"          : [],
    "css"           : [],
    "application"   : True,
    "installable"   : True,
    "auto_install"  : False,
    "external_dependencies": {
        "python": [
            "xlsxwriter",
        ]
    }
}