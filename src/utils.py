import psycopg2

def image_to_binary(image_input):
    if isinstance(image_input, bytes):
        return psycopg2.Binary(image_input)
    elif isinstance(image_input, str):
        with open(image_input, 'rb') as file:
            return psycopg2.Binary(file.read())
    else:
        raise ValueError("Invalid input type for image_to_binary function.")

def binary_to_image(binary_data, output_path):
    with open(output_path, 'wb') as file:
        file.write(binary_data)
