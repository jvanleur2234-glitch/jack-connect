---
name: invoice-generator
description: Create a professional invoice PDF for any business. Trigger on "invoice", "send invoice", "create invoice", "billing", "charge client"
---
# Invoice Generator Skill

Creates professional invoices using EasyInvoicePDF API.

## Input Collection

Collect from user:
- Client name and email
- Business name
- Service description
- Amount
- Due date
- Any additional notes

## How to Generate

Use the EasyInvoicePDF API or open the web interface with pre-filled data:
```
https://easyinvoicepdf.com/?client=[name]&amount=[amount]&description=[service]
```

Or use the API endpoint (if JackConnect has API key):
```
POST /api/invoice
Body: { client, items[], amount, due_date }
```

## Invoice Output

Download the PDF and:
1. Save to JackConnect workspace
2. Attach to client CRM record
3. Offer to email it directly

## Trigger

Automatically trigger when Jack says "invoice", "send an invoice", "charge them", "bill the client".
