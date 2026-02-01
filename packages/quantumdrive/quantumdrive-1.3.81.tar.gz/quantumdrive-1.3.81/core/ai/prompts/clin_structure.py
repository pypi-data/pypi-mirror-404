CLIN_STRUCTURE = """
### CLIN PARSING & PRICING STRUCTURE
Extract Contract Line Item Numbers (CLINs) with strict attention to hierarchy and periodicity.

**Extraction Rules:**
1.  **Hierarchy:** Distinguish between Parent CLINs (e.g., 0001) and Sub-CLINs/SLINs (e.g., 0001AA).
2.  **Periodicity:** Tag each CLIN as "Base Period", "Option Year X", or "Transition".
3.  **Attributes:** For each CLIN, extract:
    *   CLIN Number
    *   Description/Nomenclature
    *   Unit of Issue (e.g., MO, LO, EA)
    *   Quantity
    *   Contract Type (FFP, T&M, CPFF)
4.  **Not Separately Priced (NSP):** Explicitly identify items marked as NSP.
"""
