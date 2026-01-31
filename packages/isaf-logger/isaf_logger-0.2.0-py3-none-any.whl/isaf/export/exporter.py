"""
ISAF Exporter

Exports lineage data to ISAF v1.0 JSON format with compliance mappings.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from isaf.verification.hash_chain import HashChainGenerator


class ISAFExporter:
    """
    Exports ISAF lineage data to JSON files.
    
    Generates complete ISAF v1.0 compliant documents with optional
    hash chain verification and compliance framework mappings.
    """
    
    LAYER_OWNERS = {
        6: 'ML Engineer / Platform Team',
        7: 'Data Engineer / Data Science Team',
        8: 'Data Scientist / ML Engineer',
        9: 'MLOps Engineer / Deployment Team'
    }

    COMPLIANCE_MAPPINGS = {
        'eu_ai_act': {
            'name': 'EU AI Act',
            'article_mappings': {
                6: ['Article 9 - Risk Management', 'Article 15 - Accuracy'],
                7: ['Article 10 - Data Governance', 'Article 12 - Record-keeping'],
                8: ['Article 13 - Transparency', 'Article 14 - Human Oversight'],
                9: ['Article 14 - Human Oversight', 'Article 17 - Quality Management']
            }
        },
        'nist_ai_rmf': {
            'name': 'NIST AI RMF',
            'function_mappings': {
                6: ['GOVERN 1.1', 'MAP 1.1'],
                7: ['MAP 1.5', 'MEASURE 2.3'],
                8: ['MAP 1.6', 'MANAGE 1.1'],
                9: ['MANAGE 2.1', 'MANAGE 3.1', 'GOVERN 6.1']
            }
        },
        'iso_42001': {
            'name': 'ISO/IEC 42001',
            'control_mappings': {
                6: ['6.1.2 - AI System Design', '7.2 - Competence'],
                7: ['6.1.3 - Data Management', '8.2 - Data Quality'],
                8: ['6.1.4 - AI Model Development', '9.1 - Monitoring'],
                9: ['8.3 - AI System Deployment', '9.2 - Internal Audit', '10.1 - Improvement']
            }
        },
        'colorado_ai_act': {
            'name': 'Colorado AI Act (SB24-205)',
            'section_mappings': {
                6: ['Section 6-1-1702 - Duty of Care'],
                7: ['Section 6-1-1702 - Data Requirements'],
                8: ['Section 6-1-1703 - Impact Assessment'],
                9: ['Section 6-1-1704 - Disclosure Requirements', 'Section 6-1-1705 - Consumer Rights']
            }
        }
    }
    
    def export(
        self,
        lineage_data: Dict[str, Any],
        output_path: str,
        include_hash_chain: bool = True,
        compliance_mappings: Optional[List[str]] = None
    ) -> str:
        """
        Export lineage data to ISAF JSON file.
        
        Args:
            lineage_data: Complete lineage dictionary
            output_path: Path for output file
            include_hash_chain: Include cryptographic verification
            compliance_mappings: List of frameworks ('eu_ai_act', 'nist_ai_rmf', 'iso_42001')
        
        Returns:
            Path to the exported file
        """
        document = {
            'isaf_version': '1.0',
            'audit_id': str(uuid.uuid4()),
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'session_id': lineage_data.get('session_id'),
            'session_created_at': lineage_data.get('created_at'),
            'instruction_stack': self._build_stack_trace(lineage_data),
            'system_info': self._extract_system_info(lineage_data),
            'metadata': lineage_data.get('metadata', {})
        }
        
        if include_hash_chain:
            generator = HashChainGenerator()
            document['hash_chain'] = generator.generate_chain(lineage_data)
        
        if compliance_mappings:
            document['compliance'] = self._generate_compliance_mappings(
                lineage_data, 
                compliance_mappings
            )
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(document, f, indent=2)
        
        return str(output_file.absolute())
    
    def _build_stack_trace(self, lineage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build the instruction stack trace from layers."""
        layers = lineage_data.get('layers', {})
        stack = []
        
        for layer_key in sorted(layers.keys(), key=lambda x: int(x)):
            layer_num = int(layer_key)
            layer_data = layers[layer_key]
            
            stack.append({
                'layer': layer_num,
                'layer_name': layer_data.get('data', {}).get('layer_name', f'Layer {layer_num}'),
                'owner': self._get_layer_owner(layer_num),
                'logged_at': layer_data.get('logged_at'),
                'data': layer_data.get('data', {})
            })
        
        return stack
    
    def _extract_system_info(self, lineage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract system information from Layer 6."""
        layers = lineage_data.get('layers', {})
        layer6 = layers.get('6', {}).get('data', {})
        
        return layer6.get('system', {})
    
    def _generate_compliance_mappings(
        self, 
        lineage_data: Dict[str, Any],
        frameworks: List[str]
    ) -> Dict[str, Any]:
        """Generate compliance framework mappings."""
        layers = lineage_data.get('layers', {})
        logged_layers = [int(k) for k in layers.keys()]
        
        mappings = {}
        
        for framework in frameworks:
            if framework not in self.COMPLIANCE_MAPPINGS:
                continue
            
            framework_info = self.COMPLIANCE_MAPPINGS[framework]
            mapping_key = list(framework_info.keys())[1]
            framework_mappings = framework_info[mapping_key]
            
            covered = []
            missing = []
            
            for layer, requirements in framework_mappings.items():
                if layer in logged_layers:
                    covered.extend(requirements)
                else:
                    missing.extend(requirements)
            
            mappings[framework] = {
                'framework_name': framework_info['name'],
                'covered_requirements': covered,
                'missing_requirements': missing,
                'coverage_percentage': round(
                    len(covered) / (len(covered) + len(missing)) * 100, 1
                ) if (covered or missing) else 0
            }
        
        return mappings
    
    def _get_layer_owner(self, layer_num: int) -> str:
        """Get the typical owner for a layer."""
        return self.LAYER_OWNERS.get(layer_num, 'Unknown')
