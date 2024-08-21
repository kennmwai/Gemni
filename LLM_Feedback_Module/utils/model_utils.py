

def save_model_output(output_data, output_path):
    with open(output_path, "wb") as file:
        file.write(output_data)
    print(f"Output saved to {output_path}")


# Example usage
if __name__ == "__main__":
    output_data = b'This is a test output data'
    output_path = "./output_test.dat"
    save_model_output(output_data, output_path)
