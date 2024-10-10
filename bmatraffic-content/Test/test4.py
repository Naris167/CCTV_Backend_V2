# from Database import *

# save_path = "./Images/"

# def save_all_images_to_local(output_path):
#     # Fetch all image IDs
#     image_ids = fetch_all_images_from_db()
    
#     if not image_ids:
#         print("No images found in the database.")
#         return

#     # Loop through each image ID and retrieve the image
#     for img_id in image_ids:
#         retrieve_image(img_id, output_path)


# if not os.path.exists(save_path):
#     os.makedirs(save_path)

# save_all_images_to_local(save_path)