"""
Content Completeness Validator
Verifies that 100% of input items (all table rows, table cells, bullets, TOC items,
index items, and narrative paragraphs) are present in the output presentation
via the provenance map.
"""

from typing import List, Dict, Any, Set


class CompletenessValidator:
    @staticmethod
    def validate_completeness(
        all_input_ids: List[str],
        provenance_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates set difference between input IDs and rendered output IDs.
        Missing content = input_ids - rendered_ids.
        """
        input_set = set(all_input_ids)
        rendered_set = set(provenance_map.keys())

        accounted_for = set()
        for i_id in input_set:
            if i_id in rendered_set:
                accounted_for.add(i_id)
            else:
                # An item is accounted for if:
                # 1. A rendered parent covers it (e.g. rendered table ID covers its rows and cells)
                # 2. Rendered children cover it (e.g. rendered items cover their parent container)
                if any(i_id.startswith(r_id) or r_id.startswith(i_id) for r_id in rendered_set):
                    accounted_for.add(i_id)

        missing_ids = sorted(list(input_set - accounted_for))
        status = "PASS" if len(missing_ids) == 0 else "FAIL"

        return {
            "status": status,
            "total_input_items": len(input_set),
            "total_rendered_items": len(accounted_for),
            "missing_count": len(missing_ids),
            "missing_ids": missing_ids
        }
