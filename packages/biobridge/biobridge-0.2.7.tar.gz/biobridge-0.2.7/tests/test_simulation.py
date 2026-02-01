from neural_analyzer_simulation import NeuralTissueSimulation
from biobridge.tools.image_analyzer import ImageAnalyzer

def main():
    
    analyzer = ImageAnalyzer()
    
    image_path = "/Users/witoldwarchol/PycharmProjects/pythonProject/tests/image_examples/image_0.TIF"
    
    simulation = NeuralTissueSimulation(analyzer)
    
    results = simulation.analyze_and_create_objects(image_path)
    
    print("\n=== Analysis Complete ===")
    print(f"Cells detected: {len(results['cells'])}")
    print(f"Tissues created: {len(results['tissues'])}")
    
    for i, tissue in enumerate(results['tissues']):
        print(f"\nTissue {i}: {tissue.name}")
        print(f"  Type: {tissue.tissue_type}")
        print(f"  Cells: {len(tissue.cells)}")
        
        if tissue.tissue_type == "nervous":
            assessment = tissue.comprehensive_neural_assessment()
            print(f"  Synaptic Density: "
                  f"{assessment['connectivity']['synaptic_density']:.4f}")
            print(f"  Average Health: "
                  f"{assessment['cellular_health']['average_health']:.2f}")
    
    simulation.visualize_segmentation(
        "test.png"
    )
    
    simulation.export_results(
        "test.json"
    )
    
    analyzer.close()
    
    return results


if __name__ == "__main__":
    main()
