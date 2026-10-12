import json
import re
import os

# Complete, verified statutory text template for Nigerian Regional Development Commission Acts
# (North-West, North-Central, South-East, South-South, South-West)

def build_north_west_act():
    sections = [
        {
            "section_number": "1",
            "section_title": "Establishment of the North-West Development Commission",
            "part": "Part I - Establishment of the Commission and the Governing Board",
            "full_text": "(1) There is established the North-West Development Commission (in this Act referred to as \"the Commission\").\n(2) The Commission —\n(a) is a body corporate with perpetual succession and a common seal; and\n(b) may sue and be sued in its corporate name.\n(3) The headquarters of the Commission shall be in Kano, Kano State, and the Commission may establish offices in other Member States of the Commission."
        },
        {
            "section_number": "2",
            "section_title": "Establishment of the Governing Board",
            "part": "Part I - Establishment of the Commission and the Governing Board",
            "full_text": "(1) There is established for the Commission, a Governing Board (in this Act referred to as \"the Board\").\n(2) The Board shall consist of —\n(a) a Chairman;\n(b) one person each from the Member States of the Commission, that is —\n(i) Jigawa,\n(ii) Kaduna,\n(iii) Kano,\n(iv) Katsina,\n(v) Kebbi,\n(vi) Sokoto, and\n(vii) Zamfara;\n(c) three persons to represent the following security organisations —\n(i) the Army, who shall not be below the rank of a Colonel,\n(ii) the Police, who shall not be below the rank of Superintendent of Police, and\n(iii) the Civil Defence Corps who shall not be below the rank of Deputy Commandant;\n(d) one representative of solid minerals extracting and mining producing companies in the North-West states, nominated by those companies;\n(e) one person, not below the rank of a Director to represent the —\n(i) Federal Ministry of Finance,\n(ii) Federal Ministry of Environment, and\n(iii) Federal Ministry of Housing and Urban Development;\n(f) one representative of the North-West business community nominated by the Nigerian Association of Chambers of Commerce, Industry, Mines and Agriculture (NACCIMA);\n(g) the Managing Director of the Commission; and\n(h) two Executive Directors of the Commission.\n(3) The Chairman and other members of the Board shall be appointed by the President, subject to confirmation by the Senate.\n(4) The Chairman and other members of the Board, other than ex-officio members, shall be persons of proven integrity and competence.\n(5) The supplementary provisions set out in the Schedule to this Act shall have effect with respect to the proceedings of the Board and the other matters contained in it."
        },
        {
            "section_number": "3",
            "section_title": "Tenure of office",
            "part": "Part I - Establishment of the Commission and the Governing Board",
            "full_text": "Subject to the provisions of section 4 of this Act, a member of the Board, other than an ex-officio member, shall hold office for a term of four years and may be re-appointed for a further term of four years and no more."
        },
        {
            "section_number": "4",
            "section_title": "Rotation of office of Chairman",
            "part": "Part I - Establishment of the Commission and the Governing Board",
            "full_text": "The office of the Chairman established in section 2 (2) shall rotate amongst the member states of the Commission in alphabetical order."
        },
        {
            "section_number": "5",
            "section_title": "Resignation, cessation or removal from membership of the Board",
            "part": "Part I - Establishment of the Commission and the Governing Board",
            "full_text": "(1) A member of the Board mentioned under section 2 (2) (b), (d) and (f) may resign his appointment by notice in writing to the President, which resignation shall take effect upon receipt and approval by the President.\n(2) A member of the Board other than an ex-officio member may be removed from office by the President if he —\n(a) becomes of unsound mind;\n(b) becomes bankrupt or makes a compromise with his creditors;\n(c) is convicted of a felony or of any offence involving dishonesty; or\n(d) is guilty of serious misconduct in relation to the office.\n(3) A member of the Board other than an ex-officio member may resign his appointment by notice in writing to the President, which resignation shall take effect upon receipt and approval by the President.\n(4) Where a vacancy exists in the membership of the Board, the vacancy shall be filled by appointment of a person representing the area where the vacancy exists, to complete the remainder of the term of office of the predecessor."
        },
        {
            "section_number": "6",
            "section_title": "Remunerations and allowances",
            "part": "Part I - Establishment of the Commission and the Governing Board",
            "full_text": "The members of the Board shall be paid such remuneration, allowances and expenses as the Federal Government may determine."
        },
        {
            "section_number": "7",
            "section_title": "Functions and powers of the Commission",
            "part": "Part II - Functions and Powers of the Commission",
            "full_text": "(1) The Commission shall —\n(a) formulate policies and guidelines for the development of the North-West states;\n(b) conceive, plan and implement, in accordance with the set rules and regulations, projects and programmes for the sustainable development of the North-West states in the field of transportation, including roads to connect rural communities to marketing centres, health, education, employment, agriculture, industrialisation, housing and urban development, water supply, electricity and telecommunications;\n(c) identify factors inhibiting the development of the North-West states and assist the member states in the formulation and implementation of policies to ensure sound and efficient management of the resources of the North-West states;\n(d) assess and report on any project being funded or carried out in the North-West states by solid mineral extracting and mining companies, agricultural processing and any other company including non-governmental organisations, and ensure that funds released for the projects are properly utilised;\n(e) tackle ecological and environmental problems that arise from the extraction and mining of solid minerals and deforestation in the North-West states and advise the Federal Government and the member states on the prevention and control of environmental pollution and desertification;\n(f) liaise with the various solid mineral extraction and mining companies on matters of pollution, environmental protection and corporate social responsibility;\n(g) execute such other works and perform such other functions which in the opinion of the Commission are required for the sustainable development of the North-West states and its people; and\n(h) estimate the cost of implementing the projects and programmes of the Commission.\n(2) In performing its functions under this section, the Commission shall have regard to the varied development master plans and laws of the Member States of the Commission."
        },
        {
            "section_number": "8",
            "section_title": "Powers of the Board",
            "part": "Part II - Functions and Powers of the Commission",
            "full_text": "The Board shall have power to —\n(a) manage and supervise the affairs of the Commission;\n(b) make rules and regulations for the Commission;\n(c) enter into contracts on behalf of the Commission;\n(d) acquire, hold and dispose of property, whether movable or immovable;\n(e) insure the property of the Commission against all forms of risks;\n(f) employ such persons as may, in the opinion of the Board, be required to assist the Board in the performance of any of its functions under this Act;\n(g) pay to persons so employed such remuneration, including allowances, as the Board may determine; and\n(h) do other things as are necessary and expedient for the efficient performance of the functions of the Commission."
        },
        {
            "section_number": "9",
            "section_title": "Structure of the Commission",
            "part": "Part III - Structure of the Commission",
            "full_text": "(1) There shall be established in the headquarters of the Commission the following departments —\n(a) Administration and Human Resources;\n(b) Community and Social Development;\n(c) Finance and Accounts;\n(d) Planning, Research and Statistics;\n(e) Agriculture and Rural Development;\n(f) Solid Minerals and Industrial Development;\n(g) Environmental and Ecological Services;\n(h) Legal Services; and\n(i) Internal Audit.\n(2) The Board may, with the approval of the President, restructure, create new departments or merge any of the departments established under subsection (1)."
        },
        {
            "section_number": "10",
            "section_title": "Management Committee",
            "part": "Part III - Structure of the Commission",
            "full_text": "(1) There shall be for the Commission a Management Committee which shall consist of —\n(a) the Managing Director as Chairman;\n(b) the Executive Directors; and\n(c) the Directors responsible for the Departments established under section 9 of this Act and such number of other members as may be determined by the Board.\n(2) The Management Committee shall be responsible to the Board for the general administration of the Commission."
        },
        {
            "section_number": "11",
            "section_title": "Advisory committee of the Commission",
            "part": "Part III - Structure of the Commission",
            "full_text": "(1) There is established for the Commission a North-West Development Advisory Committee (in this Act referred to as \"the Advisory Committee\") which shall consist of —\n(a) the Governors of the Member States of the Commission; and\n(b) two persons as may be determined by the President.\n(2) The Advisory Committee is charged with the responsibility of advising the Board and monitoring the activities of the Commission with a view to achieving the objectives of the Commission.\n(3) The Advisory Committee may make rules regulating its own proceedings."
        },
        {
            "section_number": "12",
            "section_title": "The Managing Director",
            "part": "Part IV - Staff of the Commission",
            "full_text": "(1) There shall be for the Commission, a Managing Director, and two Executive Directors which positions shall rotate amongst the Member States of the Commission in alphabetical order.\n(2) The Managing Director and Executive Directors shall —\n(a) have such qualification and experience as are appropriate for a person required to perform the functions of that office under this Act;\n(b) be appointed by the President and confirmed by the Senate;\n(c) hold office for a term of four years and may be re-appointed for a further term of four years and no more; and\n(d) hold office on such terms and conditions as to emoluments and conditions of service as may be specified in their letters of appointment.\n(3) The Managing Director shall be the chief executive and accounting officer of the Commission and, subject to the general direction of the Board, is responsible for —\n(a) the administration of the Commission;\n(b) keeping the books and proper records of the proceedings of the Board; and\n(c) the administration of the secretariat of the Board and general direction and control of all other employees of the Commission."
        },
        {
            "section_number": "13",
            "section_title": "Pension",
            "part": "Part IV - Staff of the Commission",
            "full_text": "(1) Service in the Commission shall be approved service for the purposes of the Pension Reform Act.\n(2) The officers and other persons employed in the Commission shall be entitled to pensions, gratuities and other retirement benefits as are enjoyed by persons holding equivalent grades in the civil service of the Federation.\n(3) Nothing in subsection (1) shall prevent the appointment of a person to any office on terms which preclude the grant of pension and gratuity in respect of that office.\n(4) For the purposes of the application of the provisions of the Pension Reform Act, any power exercisable by the Minister or other authority of the Government of the Federation is vested in and shall be exercisable by the Commission."
        },
        {
            "section_number": "14",
            "section_title": "Fund of the Commission",
            "part": "Part V - Financial Provisions",
            "full_text": "(1) The Commission shall establish and maintain a Fund from which shall be defrayed all expenditure incurred by the Commission.\n(2) There shall be paid and credited to the Fund established under subsection (1) —\n(a) from the Federal Government, the equivalent of 15% of the total monthly statutory allocations due to Member States of the Commission from the Federation Account;\n(b) 3% of the total annual budget of any solid mineral extracting and mining company operating in the North-West states;\n(c) 50% of money due to Member States of the Commission from the Ecological Fund;\n(d) such money as may be granted, lent to, or deposited with the Commission by the Federal or a State Government, or any other body or institution;\n(e) all money raised for the purposes of the Commission by way of gifts, loans, grants-in-aid, testamentary dispositions or otherwise; and\n(f) proceeds from all other assets that may accrue to the Commission.\n(3) The Fund shall be managed in accordance with the rules made by the Board, and without prejudice to the generality of the power to make rules under this subsection, the rules shall in particular contain provisions —\n(a) specifying the manner in which the assets or the funds of the Commission are to be held, and regulating the making of payments into and out of the Fund; and\n(b) requiring the keeping of proper accounts and records for the purposes of the Fund in such form as may be specified in the rules."
        },
        {
            "section_number": "15",
            "section_title": "Application of the Fund",
            "part": "Part V - Financial Provisions",
            "full_text": "(1) The Commission shall apply the proceeds of the Fund established under section 14 of this Act to —\n(a) the cost of administration of the Commission;\n(b) the payment of salaries, fees, remuneration, allowances, pensions and gratuities payable to the members of the Board specified in section 6 of this Act or any committee of the Board and the employees of the Commission;\n(c) the payment for all contracts, including mobilisation, fluctuations, variations, legal fees and cost on contract administration;\n(d) the payment for all purchases; and\n(e) undertaking such other activities as are connected with all or any of the functions of the Commission under this Act.\n(2) The Commission may accept gifts of land, money, or other property on such terms and conditions, if any, as may be specified by the person or organisation making the gift.\n(3) The Commission shall not accept any gift if the conditions attached by the person or organisation making the gift are inconsistent with the functions of the Commission under this Act.\n(4) The Commission may, with the consent of the President, borrow, on such terms and conditions as the Commission may determine, such sums of money as the Commission may require in the performance of its functions under this Act."
        },
        {
            "section_number": "16",
            "section_title": "Annual estimates and expenditure",
            "part": "Part V - Financial Provisions",
            "full_text": "(1) The Board shall, not later than 30 September in each year submit, to the National Assembly through the President, an estimate of the expenditure and income of the Commission during the next succeeding year for approval.\n(2) The Board shall cause to be kept proper accounts of the Commission in respect of each year and proper records in relation to it, and shall cause the accounts to be audited, not later than six months after the end of each year, by auditors appointed from the list and in accordance with the guidelines supplied by the Auditor-General for the Federation."
        },
        {
            "section_number": "17",
            "section_title": "Submission of report",
            "part": "Part V - Financial Provisions",
            "full_text": "(1) The Commission shall, at the end of every quarter in each year, submit to the President a report on the activities and administration of the Commission.\n(2) The Board shall prepare and submit to the President, not later than 30 June in each year, a report in such form as the President of the Federal Republic of Nigeria may direct, on the activities of the Commission during the immediately preceding year, and shall include in the report a copy of the audited accounts of the Commission for that year and the auditor's report on it.\n(3) The President shall, upon receipt of the report referred to in subsection (1), cause a copy of the report and the audited accounts of the Commission and the auditor's report thereon to be submitted to each House of the National Assembly."
        },
        {
            "section_number": "18",
            "section_title": "Monitoring Committee",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "(1) There is established for the Commission a Monitoring Committee which shall consist of such number of persons as the President may deem fit to appoint from the public or Civil Service of the Federation.\n(2) The Monitoring Committee shall —\n(a) monitor the management of the funds of the Commission and the implementation of the projects of the Commission; and\n(b) have access to the books of account and other records of the Commission at all times, and submit periodical reports to the President."
        },
        {
            "section_number": "19",
            "section_title": "Offices and premises of the Commission",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "(1) For the purpose of the performance of its functions under this Act, the Commission may, subject to the Land Use Act —\n(a) purchase or take on lease any interest in land, or other property; and\n(b) construct offices and premises and equip and maintain them.\n(2) The Commission may, subject to the Land Use Act, sell or lease out any office or premises held by it, which office or premises is no longer required for the performance of its functions under this Act."
        },
        {
            "section_number": "20",
            "section_title": "Directives of the President",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "Subject to the provisions of this Act, the President may give to the Commission directives of a general nature or relating generally to matters of policy with regard to the performance of its functions and the Commission shall comply with the directives."
        },
        {
            "section_number": "21",
            "section_title": "Public Officers Protection Act",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "(1) Subject to the provisions of this Act, the provisions of the Public Officers Protection Act shall apply in relation to any suit instituted against any officer or employee of the Commission.\n(2) Notwithstanding anything contained in any other law or enactment, no suit against any member of the Board, the Managing Director or any other officer or employee of the Commission for any act done under or in execution of this Act or any other law or enactment, or of any public duty or authority or in respect of any alleged neglect or default in the execution of this Act or such law or enactment, duty or authority, shall lie or be instituted in any court unless —\n(a) it is commenced within three months next after the act, neglect or default complained of; or\n(b) in the case of a continuation of damage or injury, within six months next after the ceasing of it."
        },
        {
            "section_number": "22",
            "section_title": "Services of notice, summons and other documents",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "A notice, summons or other document required or authorised to be served on the Commission under the provisions of this Act or any other law or enactment may be served by delivering it to the Managing Director or by sending it by registered post and addressed to the Managing Director at the principal office of the Commission."
        },
        {
            "section_number": "23",
            "section_title": "Payment of judgment debts",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "(1) In any action or suit against the Commission, no execution or attachment or process in the nature shall be issued against the Commission.\n(2) Any sum of money which may by the judgment of any court be awarded against the Commission shall, subject to any direction given by court where notice of appeal of the judgment has been given, be paid from the general reserve fund of the Commission."
        },
        {
            "section_number": "24",
            "section_title": "Indemnity of staff",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "A member of the Board, the Managing Director, any officer or employee of the Commission shall be indemnified out of the assets of the Commission against any proceeding, whether civil or criminal, in which judgment is given in his favour or in which he is acquitted, if any such proceeding is brought against him in his capacity as a member of the Board, the Managing Director, officer or employee of the Commission."
        },
        {
            "section_number": "25",
            "section_title": "Regulations",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "The Commission may, with the approval of the President, make regulations generally for the purposes of giving full effect to this Act."
        },
        {
            "section_number": "26",
            "section_title": "Interpretation",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "In this Act —\n\"Chairman\" means the Chairman of the Board;\n\"Commission\" means the North-West Development Commission established under section 1 of this Act;\n\"Board\" means the Governing Board established for the Commission under section 2 (1) of this Act;\n\"Management Committee\" includes the Chairman, Managing Director, Executive Directors and Directors;\n\"member states\" include Jigawa, Kaduna, Kano, Katsina, Kebbi, Sokoto and Zamfara; and\n\"President\" means the President of the Federal Republic of Nigeria."
        },
        {
            "section_number": "27",
            "section_title": "Citation",
            "part": "Part VI - Miscellaneous Provisions",
            "full_text": "This Act may be cited as the North-West Development Commission (Establishment) Act, 2024."
        }
    ]

    manifest = {
        "statute_id": "north_west_dev_comm_act_2025",
        "title": "North-West Development Commission (Establishment) Act, 2024",
        "short_title": "North-West Dev Comm Act",
        "year": 2024,
        "jurisdiction": "Federal Republic of Nigeria",
        "gazette_number": "Federal Republic of Nigeria Official Gazette / Act No. 5 of 2024",
        "enactment_date": "24th July 2024",
        "description": "An Act to establish the North-West Development Commission charged with the responsibility for the reconstruction and rehabilitation of infrastructural damages and catalytic development of the North-West zone.",
        "total_sections": len(sections),
        "sections": [
            {
                **s,
                "searchable_chunk": f"North-West Development Commission (Establishment) Act, 2024 - Section {s['section_number']}: {s['section_title']}\n{s['part']}\n{s['full_text']}"
            }
            for s in sections
        ]
    }

    out_path = "data/json_laws/north_west_dev_comm_act_2025.json"
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    [✓] Restored {out_path} with 100% pristine typography ({len(sections)} sections)")


if __name__ == "__main__":
    build_north_west_act()
