#!/usr/bin/env python3

try:
    from pyln.client import Plugin, RpcError
    from lib import Prism, Member, PrismBinding
    import re
except ModuleNotFoundError as err:
    # OK, something is not installed?
    import json
    import sys
    getmanifest = json.loads(sys.stdin.readline())
    print(json.dumps({'jsonrpc': "2.0",
                      'id': getmanifest['id'],
                      'result': {'disable': str(err)}}))
    sys.exit(1)


plugin = Plugin()

@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):

    getinfoResult = plugin.rpc.getinfo()
    clnVersion = getinfoResult["version"]
    #searchString = 'v24.03'
    numbers = re.findall(r'v(\d+)\.', clnVersion)
    major_cln_version = int(numbers[0]) if numbers else None
    #plugin.log(f"major_cln_version: {major_cln_version}")
    if major_cln_version != None:
        if major_cln_version < 24:
            raise Exception("The BOLT12 Prism plugin is only compatible with CLN v24 and above.")

    plugin.log("prism-api initialized")

@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):

    # try:
    payment_label = invoice_payment["label"]
    #plugin.log(f"payment_label: {payment_label}")
    # invoices will always have a unique label
    invoice = plugin.rpc.listinvoices(payment_label)["invoices"][0]

    if invoice is None:
        return

    # invoices will likely be generated from BOLT 12
    if "local_offer_id" in invoice:
        offer_id = invoice["local_offer_id"]

    # TODO: return PrismBinding.get as class member rather than json
    binding = None

    try:
        binding = PrismBinding.get(plugin, offer_id)
    except Exception as e:
        plugin.log("Incoming payment not associated with prism binding. Skipping.", "info")
        return

    # try:
    amount_msat = invoice_payment['msat']
    plugin.log(f"amount_msat: {amount_msat}")
    binding.pay(amount_msat=int(amount_msat))

plugin.run()  # Run our plugin
