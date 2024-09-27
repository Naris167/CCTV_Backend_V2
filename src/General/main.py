from io import BytesIO
from get_cam_list import *
from database import retrieve_camID, add_camRecord_Ubon, add_camRecord_iTic, update_isCamOnline
from log_config import logger, log_setup
from utils import create_cctv_status_dict, detect_cctv_status


log_setup()

# List[Tuple[Cam_ID, Cam_Name, Latitude, Longitude, "Stream_Method", "Stream_Link_1"]]
cctv_list_ubon = getCamList_Ubon()

# List[Tuple["Cam_ID", "Cam_Name", "Latitude", "Longitude", "Stream_Method", "Stream_Link_1", "Stream_Link_2", 
# "Stream_Link_3", "Stream_Link_4", "Stream_Link_5", "Stream_Link_6", "Organization", "SponsorText", "LastUpdate", "is_inCity", "is_motion"]]
cctv_list_itic = getCamList_iTic()


add_camRecord_Ubon(cctv_list_ubon)
add_camRecord_iTic(cctv_list_itic)

all_cctv_ids = retrieve_camID()

offline_cctvs, online_cctvs = detect_cctv_status(all_cctv_ids, cctv_list_ubon, cctv_list_itic)
offline_cctvs = create_cctv_status_dict(offline_cctvs, False)
online_cctvs = create_cctv_status_dict(online_cctvs, True)
update_isCamOnline(offline_cctvs)
update_isCamOnline(online_cctvs)