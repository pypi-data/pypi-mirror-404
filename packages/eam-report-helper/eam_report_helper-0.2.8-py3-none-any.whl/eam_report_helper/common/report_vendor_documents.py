from datetime import datetime


class VendorDocumentsReport:
    """Report Vendor Documents"""

    def __init__(self, db, company_id: str) -> None:
        self.db = db
        self.company_id = company_id

    def key_func(self, k: dict) -> str:
        """Key function"""
        return k['Vendor Name']

    def match_expiry_date(self, vendor_doc: dict, vendor_qoc_questions: list) -> str:
        """Match expiry date"""
        expiry_date = ''

        if 'values' in vendor_doc['ocrOutput']:

            if vendor_doc['ocrOutput']['values'] != []:

                for item in vendor_doc['ocrOutput']['values']:

                    if item['key'] == 'expiry_date':

                        if item['updatedValue'] != '':
                            expiry_date = item['updatedValue']
                        else:
                            expiry_date = item['ocrValue']
            else:

                for vendor_qoc_question in vendor_qoc_questions:
                    if vendor_doc['id'] == vendor_qoc_question['vendorDocId']:
                        expiry_date = vendor_qoc_question['answer']

        else:

            for vendor_qoc_question in vendor_qoc_questions:
                if vendor_doc['id'] == vendor_qoc_question['vendorDocId']:
                    expiry_date = vendor_qoc_question['answer']

        return expiry_date

    def build_vendor_document_report(self) -> dict:
        """Build vendor document report"""

        headers = ["Vendor Name", "Document Type", "Document Name",
                   "Status", "Expiry Date", "Last Modified"]

        vendor_list_by_employer = self.db.get_results(
            query=f"SELECT c.vendorId, c.vendorName FROM c WHERE c.type = 'vendorList' AND c.employerId = '{self.company_id}'")

        results = [x['vendorId'] for x in vendor_list_by_employer]

        docs = self.db.get_results(
            query=f"SELECT c.id, c.vendorId, c.employerId, c.docType, c.docName, c.status, c.ocrOutput, c._ts FROM c WHERE c.type = 'vendorDoc' AND ARRAY_CONTAINS({results}, c.vendorId) AND c.status != 'Not Submitted'")

        vendor_doc_questions = self.db.get_results(
            query="SELECT * FROM c WHERE c.type = 'vendorDocQuestion' AND c.key = 'expiry_date'")

        results = []
        for doc in docs:

            if 'docName' in doc:
                doc_name = doc['docName']
            else:
                doc_name = ''

            expiry_date = self.match_expiry_date(doc, vendor_doc_questions)

            if 'employerId' in doc:
                if doc['employerId'] == self.company_id:

                    results.append({
                        'Vendor Name': [x['vendorName'] for x in vendor_list_by_employer if x['vendorId'] == doc['vendorId']][0],
                        'Document Type': doc['docType'],
                        'Document Name': doc_name,
                        'Status': doc['status'],
                        'Expiry Date': expiry_date,
                        'Last Modified': datetime.fromtimestamp(doc["_ts"]).strftime("%Y-%m-%d")
                    })
                else:
                    pass

            else:
                results.append({
                    'Vendor Name': [x['vendorName'] for x in vendor_list_by_employer if x['vendorId'] == doc['vendorId']][0],
                    'Document Type': doc['docType'],
                    'Document Name': doc_name,
                    'Status': doc['status'],
                    'Expiry Date': expiry_date,
                    'Last Modified': datetime.fromtimestamp(doc["_ts"]).strftime("%Y-%m-%d")
                })

        rows = sorted(results, key=self.key_func)

        return {
            'file_name': 'Vendor_Documents_Report.csv',
            'headers': headers,
            'rows': rows
        }
