SELECT
    sp.invoice_number AS id_invoice,
    sp.invoice_date,
    SUBSTRING(sp.reference_period, 1, 4) || '-' || SUBSTRING(sp.reference_period, 5) AS year_and_quarter,
    sp.accounting_year,
    sp.invoice_line_desc AS descr,
    sp.gl_account,
    sp.gl_account_desc AS glaccount_description,
    sp.calc_amount_vat_included AS invoice_amount_vat_incl,
    sp.calc_amount_vat_excluded AS invoice_amount_vat_excl,
    sp.calc_amount_eur_vat_included AS invoice_amount_vat_incl_eur,
    sp.calc_amount_eur_vat_excluded AS invoice_amount_vat_excl_eur,
    sp.calc_local_vat_percentage AS local_vat_pct,
    sp.currency,
    CASE WHEN sp.currency = 'EUR' THEN 1 ELSE (SELECT exchange_rate FROM spendloader.tb_exchange_rate er WHERE er.currency = sp.currency AND er.exchange_date = sp.invoice_date) END AS exch_rate,
    ROW_NUMBER() OVER (PARTITION BY sp.entity_code, sp.invoice_number ORDER BY sp.invoice_line_number) AS line_number,
    sp.entity_code AS entity_country,
    (SELECT en.sys_code FROM spendloader.tb_anag_entity en WHERE en.entity_code = sp.entity_code) AS sys_code,
    (SELECT cat.cat1 FROM spendloader.vw_anag_category cat WHERE cat.category_id = sp.category_id) AS id_category_1,
    (SELECT cat.cat2 FROM spendloader.vw_anag_category cat WHERE cat.category_id = sp.category_id) AS id_category_2,
    (SELECT cat.cat3 FROM spendloader.vw_anag_category cat WHERE cat.category_id = sp.category_id) AS id_category_3,
    sp.local_commodity,
    (SELECT te.team_name FROM spendloader.tb_anag_team te WHERE te.team_id = sp.team_id) AS team,
    NULL AS reconciliated_supplier,
    (SELECT sup.supplier_name FROM spendloader.tb_anag_supplier_l2 sup WHERE sup.supplier_id = sp.supplier_id) AS supplier_name_original,
    (SELECT rsup.reconciled_supplier_name FROM spendloader.tb_anag_reconciled_supplier_l2 rsup WHERE rsup.reconciled_supplier_id = (SELECT sup.reconciled_supplier_id FROM spendloader.tb_anag_supplier_l2 sup WHERE sup.supplier_id = sp.supplier_id)) AS supplier_name,
    sp.supplier_code AS supplier_sap_code,
    (SELECT case
	    when sup.intragroup IS true then 1
	    else 0
	    END
    FROM spendloader.tb_anag_supplier_l2 sup WHERE sup.supplier_id = sp.supplier_id) AS intragroup,
    (SELECT CASE
        WHEN sup.out_of_scope IS TRUE THEN 'Out of Scope'
        WHEN sup.legal IS TRUE THEN 'Legal'
        ELSE NULL
    END
    FROM spendloader.tb_anag_supplier_l2 sup WHERE sup.supplier_id = sp.supplier_id) AS supplier_tag,
    (SELECT sup.ivalua_code FROM spendloader.tb_anag_supplier_l2 sup WHERE sup.supplier_id = sp.supplier_id) AS supplier_ivalua_code
FROM spendloader.tb_spend_l2 sp
WHERE sp.reference_period = '{reference_period}'
ORDER BY sp.entity_code, sp.invoice_number, line_number;
