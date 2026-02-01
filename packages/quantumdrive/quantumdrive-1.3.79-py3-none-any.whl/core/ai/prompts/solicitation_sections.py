SOLICITATION_SECTIONS = """
### SOLICITATION SECTION EXTRACTION
Analyze the solicitation and extract the standard Uniform Contract Format (UCF) sections and the proposal response/evaluation sections.

**Standard UCF Sections:**
*   **Section C:** Description/Specifications/Statement of Work (PWS/SOW/SOO).
*   **Section L:** Instructions, Conditions, and Notices to Offerors (Proposal Instructions).
*   **Section M:** Evaluation Factors for Award (Evaluation Criteria).

For each detected response section/volume, return:
* `name`: the normalized name from the list above.
* `title`: the exact heading/title text from the solicitation (if present).
* `page_number`: printed/logical page where the section begins (null if unknown).
* `metadata.page_number`: duplicate the page number here as well.

"""
