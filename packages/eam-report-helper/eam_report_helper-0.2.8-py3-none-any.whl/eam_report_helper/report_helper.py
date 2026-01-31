import os
import base64
import logging

from .common.report_helper_forms import FormReportHelper
from .common.helpers import generate_csv

from .common.report_safety_tickets import SafetyTicketsReport
from .common.report_vendor_documents import VendorDocumentsReport
from .common.report_emp_questions import EmpQuestionsReport
from .common.report_vendor_deficiencies import VendorDeficienciesReport
from .common.report_newly_added_vendors import NewlyAddedVendorReport
from .common.report_operator_tickets import OperatorTicketReport

from eam_db_helper import db
from eam_b2c_helper import b2c

logger = logging.getLogger("azure")
logger.setLevel(logging.WARN)


class ReportHelper:
    """Report Helper"""

    def __init__(self, company_id: str, branch_id: str) -> None:
        self.company_id = company_id
        self.db = db.DatabaseHelper({
            'account_uri': os.environ['COSMOS_ACCOUNT_URI'],
            'key': os.environ['COSMOS_KEY'],
            'db_name': os.environ['COSMOS_DATABASE'],
            'container_name': os.environ['COSMOS_CONTAINER']
        })
        self.b2c_helper = b2c.B2CHelper({
            "grant_type": "client_credentials",
            "user_mgmt_client_id": os.environ["B2C_USER_MANAGEMENT_APP_CLIENT_ID"],
            "scope": "https://graph.microsoft.com/.default",
            "user_mgmt_client_secret": os.environ[
                "B2C_USER_MANAGEMENT_APP_CLIENT_SECRET"
            ],
            "tenant_id": os.environ["B2C_TENANT_ID"],
            "ext_app_client_id": os.environ["B2C_EXTENSION_APP_CLIENT_ID"],
        })
        self.branch_id = branch_id

    def assemble_data(self, column_names: list, rows: list, file_name: str) -> str:
        """Assemble data into csv and return binary string."""
        generate_csv(
            column_names, file_name, rows)
        data = open(file_name, "rb").read()
        base64_string = base64.b64encode(data)
        os.remove(file_name)
        return base64_string

    def build_report(self, report_id: str) -> list:
        """Build report based on report_id"""

        match report_id:

            case '16918672-f971-42ce-bb16-c0ea46555321':
                results = SafetyTicketsReport(
                    self.db, self.company_id, self.b2c_helper).build_safety_ticket_report(self.branch_id)

            case 'd8cba0aa-b3d8-4efa-a50d-6b85acf5569c':
                results = VendorDocumentsReport(
                    self.db, self.company_id).build_vendor_document_report()

            case 'c3fc0792-37d9-40a3-827f-30d2260701d8':
                results = EmpQuestionsReport(
                    self.db, self.company_id).build_emp_questions_report()

            case '91d72e1c-c280-4946-a0bd-37979f70652d':
                results = VendorDeficienciesReport(
                    self.db, self.company_id).build_vendor_deficiencies_report()

                for row in results['rows']:
                    del row['vendor_id']

                results['headers'] = [x for x in results['rows'][0].keys()]

            case 'cecee74f-2f2f-46d5-8fb3-3e3e624f7587':
                results = FormReportHelper(self.db, self.b2c_helper).get_form_report(
                    "bbb961a1-e9ab-4419-bb21-34f4515e3997", "Insignia_IncidentReport_Tracking.csv", self.branch_id)

            case 'dc9b4bb1-91d6-4b37-aa9d-ee53cc7209b5':
                results = FormReportHelper(self.db, self.b2c_helper).get_form_report(
                    "19ae3e00-bfb9-4105-8f44-7e5bb740afc8", "Insignia_NearMiss_HazID_Tracking.csv", self.branch_id)

            case '57dcd8cd-49bb-4ebc-8c6c-5db3c360d308':
                results = FormReportHelper(self.db, self.b2c_helper).get_form_report(
                    "b3e979a8-19e0-49bb-b5dd-504df0b056bc", "Insignia_RegulatoryCorrectiveAction_Tracking.csv", self.branch_id)

            case 'dae860b7-3ea7-49a2-9d25-c95fedd42c60':
                results = NewlyAddedVendorReport(
                    self.db, self.company_id).build_saturn_report()

            case '0197faf6-da1a-424b-ad79-807519926737':
                vendor_deficiency_results = VendorDeficienciesReport(
                    self.db, self.company_id).build_vendor_deficiencies_report()

                results = OperatorTicketReport(
                    self.db, self.company_id, vendor_deficiency_results).build_operator_tickets_report()

        return self.assemble_data(results['headers'], results['rows'], results['file_name'])
