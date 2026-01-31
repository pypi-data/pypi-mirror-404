import datetime


class NewlyAddedVendorReport:
    def __init__(self, db, company_id):
        self.db = db
        self.company_id = company_id

    def build_saturn_report(self):

        # build uniz timestamp of 30 days ago
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        thirty_days_ago = int(thirty_days_ago.timestamp())

        results = self.db.get_results(
            query=f"SELECT * FROM c where c.type = 'vendorList' and c.employerId = '{self.company_id}' and c.vendorDates.added >= {thirty_days_ago} order by c.vendorDates.added desc")

        rows = []
        for item in results:
            if item['vendorDates']['added'] != '':

                item['vendorDates']['added'] = datetime.datetime.fromtimestamp(
                    item['vendorDates']['added']).strftime('%Y-%m-%d')

                rows.append({
                    'Vendor Name': item['vendorName'],
                    'Date Vendor Added': item['vendorDates']['added'],
                    'Vendor City': item['vendorAddress']['city'],
                    'Vendor Admin Name': item['vendorAccountAdmin']['name'],
                    'Vendor Admin Email': item['vendorAccountAdmin']['email'],
                    'Vendor Admin Phone': item['vendorAccountAdmin']['phone'],
                    'Rating': item['vendorOverallRating'],
                    'Current Deficiencies': '\n'.join(item['vendorOverallItems'])
                })

        return {
            'file_name': 'Added_Vendors.xlsx',
            'rows': rows,
            'headers': [x for x in rows[0].keys()] if len(rows) > 0 else []
        }
