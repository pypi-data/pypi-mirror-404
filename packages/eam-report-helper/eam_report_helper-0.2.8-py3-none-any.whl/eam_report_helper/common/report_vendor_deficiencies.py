from datetime import datetime
from eam_db_helper import db


class VendorDeficienciesReport:
    """Vendor Deficiencies Report"""

    def __init__(self, db, company_id: str) -> None:
        self.db = db
        self.company_id = company_id

    def get_ratings_updated(self, vendor_list: dict) -> dict:
        """Get ratings updated"""
        if ('ratingsUpdated' in vendor_list) and (vendor_list['ratingsUpdated'] != ''):

            return {
                'dateRatingApplied': datetime.fromtimestamp(
                    int(vendor_list['ratingsUpdated'])).strftime('%Y-%m-%d'),
                'daysSinceRatingApplied': (
                    datetime.now() - datetime.fromtimestamp(int(vendor_list['ratingsUpdated']))).days
            }
        else:
            return {
                'dateRatingApplied': '',
                'daysSinceRatingApplied': ''
            }

    def split_vendor_list_by_deficiency(self, vendor_list: dict) -> list:
        """Split vendor list by deficiency"""
        new_list = []

        try:
            tags = [x['text'] for x in vendor_list['tags']]
        except KeyError:
            tags = []

        if ('vendorOverallItems' in vendor_list) and (len(vendor_list['vendorOverallItems']) > 1):
            for deficiency in vendor_list['vendorOverallItems']:
                new_list.append({
                    'vendor_id': vendor_list['vendorId'],
                    'vendorName': vendor_list['vendorName'],
                    'vendorSubscriptionType': vendor_list['vendorSubscriptionType'],
                    'tags': tags,
                    'vendorOverallRating': vendor_list['vendorOverallRating'],
                    'vendorDeficiency': deficiency,
                    'ratingsUpdated': vendor_list['ratingsUpdated'],
                    'vendorAccountAdmin': vendor_list['vendorAccountAdmin']
                })

        else:
            new_list.append({
                'vendor_id': vendor_list['vendorId'],
                'vendorName': vendor_list['vendorName'],
                'vendorSubscriptionType': vendor_list['vendorSubscriptionType'],
                'tags': tags,
                'vendorOverallRating': vendor_list['vendorOverallRating'],
                'vendorDeficiency': [x for x in vendor_list['vendorOverallItems']][0] if len(vendor_list['vendorOverallItems']) > 0 else '',
                'ratingsUpdated': vendor_list['ratingsUpdated'],
                'vendorAccountAdmin': vendor_list['vendorAccountAdmin']
            })

        return new_list

    def build_vendor_deficiencies_report_common(self, vendor_lists) -> dict:
        formatted_list = []
        for vendor_list in vendor_lists:
            vendor_list['ratingsUpdated'] = self.get_ratings_updated(
                vendor_list)

            vendor_list: list = self.split_vendor_list_by_deficiency(
                vendor_list)

            for item in vendor_list:
                item['tags'] = '\n'.join(item['tags'])

                formatted_list.append({
                    'vendor_id': item['vendor_id'],
                    'Vendor Name': item['vendorName'],
                    'Subscription Type': item['vendorSubscriptionType'],
                    'Vendor Tags': item['tags'],
                    'Vendor Rating': item['vendorOverallRating'],
                    'Current Deficiencies': item['vendorDeficiency'],
                    'Date Rating Applied': item['ratingsUpdated']['dateRatingApplied'],
                    'Days Since Rating Applied': item['ratingsUpdated']['daysSinceRatingApplied'],
                    'Admin Name': item['vendorAccountAdmin']['name'],
                    'Admin Email': item['vendorAccountAdmin']['email'],
                    'Admin Phone': item['vendorAccountAdmin']['phone']
                })

        return formatted_list

    def add_internal_ids_to_report(self, formatted_list: list, vendor_monitor_config: dict, vendor_lists: list) -> list:
        """Add internal ids to report"""
        for item in formatted_list:
            internal_column_headers = vendor_monitor_config['employerVendorLabels']
            for header in internal_column_headers:
                item[header] = ''

        for item in formatted_list:
            for vendor in vendor_lists:
                if item['vendor_id'] == vendor['vendorId']:
                    if 'employerVendorIds' in vendor:
                        for internal_id in vendor['employerVendorIds']:
                            index = vendor['employerVendorIds'].index(
                                internal_id)
                            if index < len(vendor_monitor_config['employerVendorLabels']):
                                item[vendor_monitor_config['employerVendorLabels']
                                     [index]] = internal_id

        return formatted_list

    def build_vendor_deficiencies_report(self) -> dict:
        """Build vendor deficiencies report"""
        vendor_lists = self.db.get_results(
            query=f"SELECT c.vendorId, c.vendorName, c.vendorSubscriptionType, c.tags, c.vendorOverallRating, c.vendorOverallItems, c.employerDates.ratingsUpdated,\
                c.vendorAccountAdmin, c.employerVendorIds from c where c.type = 'vendorList'AND c.employerId = '{self.company_id}'")

        vendor_monitor_config = self.db.get_result(
            query=f"SELECT * from c where c.type = 'vendorMonitorConfig' AND c.employerId = '{self.company_id}'")

        formatted_list = self.build_vendor_deficiencies_report_common(
            vendor_lists)

        if vendor_monitor_config != {}:
            formatted_list = self.add_internal_ids_to_report(
                formatted_list, vendor_monitor_config, vendor_lists)

        return {
            'file_name': 'Def_Report.csv',
            'headers': list(formatted_list[0].keys()),
            'rows': formatted_list
        }
