SUPERADMIN_MODULES = [
    'user_list', 'user_add', 'user_edit', 'profile_view', 'profile_update', 'add_department',
    'role_list', 'role_add', 'role_edit', 'role_delete', 'permission_role', 'permission_update',
    'module_list', 'module_add', 'module_edit', 'module_delete', 'module_sync',
    'module_group_list', 'module_group_save', 'module_group_delete'
]

MODULE_LAYOUT = {
    "Dashboard": {
        "mainsystem:dashboard": {
            "label": "Dashboard",
            "icon": "bi-speedometer2",
            "children": []
        }
    },
    "mainsystem": {
        "mainsystem:user_list": {
            "label": "User Management",
            "icon": "bi-people",
            "children": [
                "mainsystem:user_create", "mainsystem:user_edit", "mainsystem:user_delete",
                "mainsystem:profile_view", "mainsystem:add_department",
                "mainsystem:edit_department", "mainsystem:delete_department"
            ]
        },
        "mainsystem:role_list": {
            "icon": "bi-person-badge",
            "children": [
                "mainsystem:role_add", "mainsystem:role_edit", "mainsystem:role_delete",
                "mainsystem:permission_role", "mainsystem:permission_update"
            ]
        },
        "mainsystem:module_list": {
            "icon": "bi-box",
            "children": [
                "mainsystem:module_add", "mainsystem:module_edit", "mainsystem:module_delete",
                "mainsystem:module_sync", "mainsystem:module_group_list",
                "mainsystem:module_group_save", "mainsystem:module_group_delete"
            ]
        }
    },
    "Patient Management": {
        "diagnostics:patient_list": {
            "label": "Patient Registration",
            "icon": "bi-person-plus",
            "children": [
                "diagnostics:patient_create", "diagnostics:patient_edit",
                "diagnostics:patient_delete", "diagnostics:patient_list"
            ]
        },
        "diagnostics:ipd_admission_list": {
            "label": "IPD Admission",
            "icon": "bi-hospital",
            "children": [
                "diagnostics:ipd_admit", "diagnostics:ipd_transfer",
                "diagnostics:ipd_discharge", "diagnostics:ipd_cancel", "diagnostics:ipd_admission_list"
            ]
        },
        "diagnostics:history": {
            "label": "Patient History",
            "icon": "bi-clock-history",
            "children": [
                "diagnostics:history_view", "diagnostics:history_print", "diagnostics:history_export"
            ]
        },
        "diagnostics:discharge_summary": {
            "label": "Discharge Summary",
            "icon": "bi-file-earmark-medical",
            "children": [
                "diagnostics:discharge_create", "diagnostics:discharge_edit",
                "diagnostics:discharge_print", "diagnostics:discharge_list"
            ]
        }
    },
    "Diagnostics": {
        "diagnostics:report_patient_list": {
            "label": "Patient Reports",
            "icon": "bi-clipboard",
            "children": [
                "diagnostics:advice_create", "diagnostics:advice_edit",
                "diagnostics:advice_cancel", "diagnostics:report_detail"
            ]
        },
        "diagnostics:sample_receive": {
            "label": "Sample Receive",
            "icon": "bi-droplet",
            "children": [
                "diagnostics:sample_receive", "diagnostics:sample_reject", "diagnostics:sample_list"
            ]
        },
        "diagnostics:test_entry": {
            "label": "Test Entry",
            "icon": "bi-flask",
            "children": [
                "diagnostics:test_create", "diagnostics:test_edit",
                "diagnostics:test_delete", "diagnostics:test_list"
            ]
        },
        "diagnostics:report_entry": {
            "label": "Report Entry",
            "icon": "bi-file-earmark-text",
            "children": [
                "diagnostics:report_create", "diagnostics:report_edit",
                "diagnostics:report_approve", "diagnostics:report_print"
            ]
        }
    },
    "Billing & Payments": {
        "diagnostics:advice_invoice_list": {
            "label": "Invoice Management",
            "icon": "bi-receipt",
            "icon_unicode": "f543",
            "class_name": "dh_soft.view.billing.InvoiceList",
            "children": [
                "diagnostics:invoice_create", "diagnostics:invoice_edit",
                "diagnostics:payment_collect", "diagnostics:invoice_cancel"
            ]
        },
        "diagnostics:collection_list": {
            "label": "Collection List",
            "icon": "bi-arrow-counterclockwise",
            "class_name": "dh_soft.view.billing.CollectionList",
            "children": [
                "diagnostics:PaymentCreate", "diagnostics:refund_approve", "diagnostics:PaymentList"
            ]
        },
        "billing:refund": {
            "label": "Refund Processing",
            "icon": "bi-arrow-counterclockwise",
            "children": [
                "billing:refund_create", "billing:refund_approve", "billing:refund_list"
            ]
        },
        "billing:discount": {
            "label": "Discount Approval",
            "icon": "bi-percent",
            "children": [
                "billing:discount_request", "billing:discount_approve", "billing:discount_list"
            ]
        },
        "billing:due": {
            "label": "Due Management",
            "icon": "bi-exclamation-circle",
            "children": [
                "billing:due_list", "billing:due_collect", "billing:due_report"
            ]
        }
    },
    "Test & Package Setup": {
        "diagnostics:test_group_list": {
            "label": "Test Master",
            "icon": "bi-list-check",
            "class_name": "dh_soft.view.test.TestMasterPanel",
            "children": [
                "diagnostics:test_group_create", "diagnostics:test_edit", "diagnostics:test_delete", "diagnostics:test_group_list"
            ]
        },
        "diagnostics:test_category_list": {
            "label": "Test Category",
            "icon": "bi-list-check",
            "children": [
                "diagnostics:test_category_create", "diagnostics:test_edit", "diagnostics:test_delete", "diagnostics:test_category_list"
            ]
        },
        "diagnostics:test_item_list": {
            "label": "Test Item List",
            "icon": "bi-list-check",
            "children": [
                "diagnostics:test_item_create", "diagnostics:test_item_edit", "diagnostics:test_item_delete", "diagnostics:test_item_list"
            ]
        },
        "setup:package": {
            "label": "Package Setup",
            "icon": "bi-box-seam",
            "children": [
                "setup:package_create", "setup:package_edit", "setup:package_delete", "setup:package_list"
            ]
        },
        "setup:rate": {
            "label": "Rate Setup",
            "icon": "bi-currency-dollar",
            "children": [
                "setup:rate_create", "setup:rate_edit", "setup:rate_list"
            ]
        }
    },
    "Doctor & Referrer": {
        "diagnostics:ConsultantReferrerList": {
            "label": "Doctor/Referrer Management",
            "icon": "bi-person-badge",
            "icons_unicode": "f2bd",
            "class_name": "dh_soft.view.consultant.ConsultantReferrerList",
            "children": [
                "diagnostics:doctor_referrer_create", "staff:doctor_referrer_edit", "staff:ConsultantReferrerList"
            ]
        },
        "staff:staff": {
            "label": "Staff Management",
            "icon": "bi-people",
            "children": [
                "staff:staff_create", "staff:staff_edit", "staff:staff_list"
            ]
        },
        "staff:shift": {
            "label": "Shift & Attendance",
            "icon": "bi-calendar-check",
            "children": [
                "staff:shift_create", "staff:shift_edit", "staff:attendance_list"
            ]
        }
    },
    "IPD Workflow": {
        "ipd:admission": {
            "label": "Admission & Bed Allocation",
            "icon": "bi-hospital",
            "children": [
                "ipd:admit", "ipd:transfer", "ipd:bed_assign", "ipd:cancel"
            ]
        },
        "ipd:nursing": {
            "label": "Nursing Notes",
            "icon": "bi-journal-text",
            "children": [
                "ipd:nursing_note_create", "ipd:nursing_note_edit", "ipd:nursing_note_list"
            ]
        },
        "ipd:medication": {
            "label": "Medication Chart",
            "icon": "bi-capsule",
            "children": [
                "ipd:medication_entry", "ipd:medication_edit", "ipd:medication_list"
            ]
        },
        "ipd:progress": {
            "label": "Progress Notes",
            "icon": "bi-graph-up",
            "children": [
                "ipd:progress_note_create", "ipd:progress_note_edit", "ipd:progress_note_list"
            ]
        }
    },
    "mainsystem & Finance": {
        "finance:collection": {
            "label": "Daily Collection",
            "icon": "bi-cash-coin",
            "children": [
                "finance:collection_view", "finance:collection_export"
            ]
        },
        "finance:ledger": {
            "label": "Ledger Summary",
            "icon": "bi-journal-bookmark",
            "children": [
                "finance:ledger_view", "finance:ledger_export"
            ]
        },
        "finance:bank": {
            "label": "Bank & Mobile Payments",
            "icon": "bi-bank",
            "children": [
                "finance:bank_entry", "finance:bank_reconcile", "finance:bank_report"
            ]
        }
    },
    "Inventory & Store": {
        "inventory:item": {
            "label": "Item Master",
            "icon": "bi-box",
            "children": [
                "inventory:item_create", "inventory:item_edit", "inventory:item_list"
            ]
        },
        "inventory:stock": {
            "label": "Stock In/Out",
            "icon": "bi-arrow-left-right",
            "children": [
                "inventory:stock_in", "inventory:stock_out", "inventory:stock_report"
            ]
        },
        "inventory:supplier": {
            "label": "Supplier Management",
            "icon": "bi-truck",
            "children": [
                "inventory:supplier_create", "inventory:supplier_edit", "inventory:supplier_list"
            ]
        }
    },
    "Admin & Configuration": {
        "admin:user": {
            "label": "User Management",
            "icon": "bi-person-gear",
            "children": [
                "admin:user_create", "admin:user_edit", "admin:user_delete", "admin:user_list"
            ]
        },
        "admin:role": {
            "label": "Role & Permission",
            "icon": "bi-shield-lock",
            "children": [
                "admin:role_create", "admin:role_edit", "admin:role_delete",
                "admin:permission_assign", "admin:permission_matrix"
            ]
        },
        "admin:settings": {
            "label": "System Settings",
            "icon": "bi-gear",
            "children": [
                "admin:config_general", "admin:config_billing", "admin:config_reports"
            ]
        },
        "admin:audit": {
            "label": "Audit Logs",
            "icon": "bi-clipboard-data",
            "children": [
                "admin:audit_view", "admin:audit_export"
            ]
        },
        "admin:backup": {
            "label": "Backup & Restore",
            "icon": "bi-cloud-arrow-up",
            "children": [
                "admin:backup_create", "admin:backup_restore", "admin:backup_list"
            ]
        }
    },
    "Reports & Analytics": {
        "reports:daily_summary": {
            "label": "Daily Summary",
            "icon": "bi-bar-chart",
            "children": [
                "reports:summary_view", "reports:summary_export"
            ]
        },
        "reports:test_collection": {
            "label": "Test-wise Collection",
            "icon": "bi-graph-up-arrow",
            "children": [
                "reports:test_collection_view", "reports:test_collection_export"
            ]
        },
        "reports:doctor_advice": {
            "label": "Doctor-wise Advice",
            "icon": "bi-person-lines-fill",
            "children": [
                "reports:doctor_advice_view", "reports:doctor_advice_export"
            ]
        },
        "reports:patient_trend": {
            "label": "Patient Visit Trends",
            "icon": "bi-calendar-range",
            "children": [
                "reports:trend_view", "reports:trend_chart"
            ]
        },
        "reports:finance": {
            "label": "Finance Reports",
            "icon": "bi-file-earmark-spreadsheet",
            "children": [
                "reports:collection_report", "reports:due_report",
                "reports:discount_report", "reports:refund_report"
            ]
        }
    }

}
