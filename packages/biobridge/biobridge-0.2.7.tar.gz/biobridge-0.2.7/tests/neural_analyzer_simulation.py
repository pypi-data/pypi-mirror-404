import numpy as np
import cv2
from typing import  Dict, Optional, Tuple
from skimage import measure


class NeuralTissueSimulation:
    def __init__(self, image_analyzer):
        self.analyzer = image_analyzer
        self.processed_image = None
        self.cells = []
        self.tissues = []
        
    def load_and_preprocess_image(
        self, image_path: str
    ) -> Tuple[any, np.ndarray]:
        raw_image = self.analyzer.load_image(image_path)
        img_array = self.analyzer.ij.py.from_java(raw_image)
        
        if hasattr(img_array, 'values'):
            img_array = img_array.values
        img_array = np.asarray(img_array)
        
        if len(img_array.shape) > 2:
            if len(img_array.shape) == 3:
                grayscale = np.dot(
                    img_array[..., :3], [0.2989, 0.5870, 0.1140]
                )
            else:
                grayscale = img_array.mean(axis=tuple(
                    range(2, len(img_array.shape))
                ))
        else:
            grayscale = img_array
        
        if grayscale.ndim > 2:
            grayscale = grayscale.squeeze()
            while grayscale.ndim > 2:
                grayscale = grayscale[0]
        
        grayscale = np.asarray(grayscale)
        grayscale = grayscale.astype(np.float32)
        grayscale = (
            (grayscale - grayscale.min()) / 
            (grayscale.max() - grayscale.min()) * 255
        )
        grayscale = grayscale.astype(np.uint8)
        
        processed_imagej = self.analyzer.ij.py.to_java(grayscale)
        
        self.processed_image = grayscale
        
        return processed_imagej, grayscale
    
    def analyze_and_create_objects(
        self, image_path: str, dna: Optional[str] = None
    ) -> Dict[str, any]:
        imagej_image, grayscale_array = (
            self.load_and_preprocess_image(image_path)
        )
        
        print(f"Processing image shape: {grayscale_array.shape}")
        print(f"Image dtype: {grayscale_array.dtype}")
        print(f"Image range: [{grayscale_array.min()}, "
              f"{grayscale_array.max()}]")
        
        self.cells = self.analyzer.analyze_cells(imagej_image, dna)
        print(f"Detected {len(self.cells)} cells")
        
        neurons = [c for c in self.cells if c.cell_type == "neuron"]
        print(f"Found {len(neurons)} neurons")
        
        nuclei_labeled = self.analyzer.identify_primary_objects(
            imagej_image
        )
        cell_bodies_labeled = (
            self.analyzer.identify_secondary_objects(nuclei_labeled)
        )
        
        tissue_mask = cell_bodies_labeled > 0
        labeled_tissue = measure.label(tissue_mask)
        
        grayscale_np = np.asarray(grayscale_array)
        if hasattr(grayscale_np, 'values'):
            grayscale_np = grayscale_np.values
        grayscale_np = np.asarray(grayscale_np)
        
        tissue_props_list = measure.regionprops(
            labeled_tissue, grayscale_np
        )
        
        self.tissues = []
        for idx, tissue_props in enumerate(tissue_props_list):
            tissue_label = tissue_props.label
            tissue_region_mask = labeled_tissue == tissue_label
            
            tissue_cells = []
            for cell_idx, cell in enumerate(self.cells):
                cell_label = cell_idx + 1
                if cell_label <= np.max(cell_bodies_labeled):
                    cell_mask = cell_bodies_labeled == cell_label
                    overlap = np.logical_and(
                        cell_mask, tissue_region_mask
                    )
                    if np.any(overlap):
                        tissue_cells.append(cell)
            
            tissue_properties = {
                'area': tissue_props.area,
                'perimeter': tissue_props.perimeter,
                'mean_intensity': tissue_props.mean_intensity,
                'centroid': tissue_props.centroid,
                'eccentricity': tissue_props.eccentricity,
                'solidity': tissue_props.solidity,
                'label': tissue_label
            }
            
            tissue_neurons = [
                c for c in tissue_cells if c.cell_type == "neuron"
            ]
            
            if tissue_neurons:
                tissue_obj = (
                    self.analyzer.create_neural_tissue_object(
                        idx, "nervous", tissue_properties, 
                        tissue_neurons
                    )
                )
            else:
                tissue_type = self.analyzer.determine_tissue_type(
                    tissue_properties
                )
                tissue_obj = self.analyzer.create_tissue_object(
                    idx, tissue_type, tissue_properties, tissue_cells
                )
            
            self.tissues.append(tissue_obj)
        
        print(f"Created {len(self.tissues)} tissue objects")
        
        return {
            'cells': self.cells,
            'tissues': self.tissues,
            'image_shape': grayscale_array.shape,
            'summary': self.generate_summary()
        }
    
    def generate_summary(self) -> Dict[str, any]:
        total_cells = len(self.cells)
        neuron_count = sum(
            1 for c in self.cells if c.cell_type == "neuron"
        )
        
        cell_type_counts = {}
        for cell in self.cells:
            cell_type = cell.cell_type
            cell_type_counts[cell_type] = (
                cell_type_counts.get(cell_type, 0) + 1
            )
        
        tissue_type_counts = {}
        for tissue in self.tissues:
            tissue_type = tissue.tissue_type
            tissue_type_counts[tissue_type] = (
                tissue_type_counts.get(tissue_type, 0) + 1
            )
        
        neural_tissues = [
            t for t in self.tissues if t.tissue_type == "nervous"
        ]
        
        summary = {
            'total_cells': total_cells,
            'total_neurons': neuron_count,
            'cell_type_distribution': cell_type_counts,
            'total_tissues': len(self.tissues),
            'tissue_type_distribution': tissue_type_counts,
            'neural_tissue_count': len(neural_tissues),
            'average_cell_health': (
                np.mean([c.health for c in self.cells]) 
                if self.cells else 0
            )
        }
        
        if neural_tissues:
            neural_metrics = []
            for nt in neural_tissues:
                metrics = nt.comprehensive_neural_assessment()
                neural_metrics.append(metrics)
            
            summary['neural_tissue_metrics'] = neural_metrics
        
        return summary
    
    def visualize_segmentation(
        self, output_path: str = None
    ) -> np.ndarray:
        if self.processed_image is None:
            raise ValueError("No processed image available")
        
        overlay = cv2.cvtColor(
            self.processed_image, cv2.COLOR_GRAY2BGR
        )
        
        nuclei_labeled = self.analyzer.identify_primary_objects(
            self.analyzer.ij.py.to_java(self.processed_image)
        )
        cell_bodies_labeled = (
            self.analyzer.identify_secondary_objects(nuclei_labeled)
        )
        
        contours_nuclei, _ = cv2.findContours(
            (nuclei_labeled > 0).astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(overlay, contours_nuclei, -1, (0, 255, 0), 1)
        
        contours_cells, _ = cv2.findContours(
            (cell_bodies_labeled > 0).astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(overlay, contours_cells, -1, (255, 0, 0), 1)
        
        if output_path:
            cv2.imwrite(output_path, overlay)
        
        return overlay
    
    def export_results(
        self, output_path: str
    ) -> None:
        import json
        
        results = {
            'summary': self.generate_summary(),
            'cells': [],
            'tissues': []
        }
        
        for cell in self.cells:
            cell_data = {
                'name': cell.name,
                'type': cell.cell_type,
                'health': cell.health,
                'age': cell.age
            }
            
            if cell.cell_type == "neuron":
                cell_data.update({
                    'soma_diameter': cell.soma_diameter,
                    'axon_length': cell.axon_length,
                    'dendrite_count': cell.dendrite_count,
                    'synapse_count': cell.synapse_count,
                    'neurotransmitters': cell.neurotransmitter_types
                })
            
            results['cells'].append(cell_data)
        
        for tissue in self.tissues:
            tissue_data = {
                'name': tissue.name,
                'type': tissue.tissue_type,
                'cell_count': len(tissue.cells),
                'growth_rate': tissue.growth_rate,
                'healing_rate': tissue.healing_rate
            }
            
            if tissue.tissue_type == "nervous":
                tissue_data.update({
                    'neural_density': tissue.neural_density,
                    'synaptic_connectivity': (
                        tissue.synaptic_connectivity
                    ),
                    'myelination_percentage': (
                        tissue.myelination_percentage
                    )
                })
            
            results['tissues'].append(tissue_data)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results exported to {output_path}")


def run_simulation(
    image_path: str, 
    image_analyzer,
    output_dir: str = "/mnt/user-data/outputs"
) -> Dict[str, any]:
    simulation = NeuralTissueSimulation(image_analyzer)
    
    results = simulation.analyze_and_create_objects(image_path)
    
    print("\n=== Simulation Summary ===")
    print(f"Total Cells: {results['summary']['total_cells']}")
    print(f"Total Neurons: {results['summary']['total_neurons']}")
    print(f"Cell Types: {results['summary']['cell_type_distribution']}")
    print(f"Total Tissues: {results['summary']['total_tissues']}")
    print(f"Tissue Types: "
          f"{results['summary']['tissue_type_distribution']}")
    print(f"Average Cell Health: "
          f"{results['summary']['average_cell_health']:.2f}")
    
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    visualization = simulation.visualize_segmentation(
        os.path.join(output_dir, "segmentation_overlay.png")
    )
    
    simulation.export_results(
        os.path.join(output_dir, "simulation_results.json")
    )
    
    return results
