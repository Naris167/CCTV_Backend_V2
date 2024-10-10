from io import BytesIO
from get_cam_list import *
from database import retrieve_camID, add_camRecord_Ubon, add_camRecord_iTic, update_isCamOnline
from utils.log_config import logger, log_setup
from utils import create_cctv_status_dict, detect_cctv_status, process_cctv_names


log_setup()

# List[Tuple[Cam_ID, Cam_Name, Latitude, Longitude, "Stream_Method", "Stream_Link_1"]]
cctv_list_ubon = getCamList_Ubon()

# List[Tuple["Cam_ID", "Cam_Name", "Latitude", "Longitude", "Stream_Method", "Stream_Link_1", "Stream_Link_2", 
# "Stream_Link_3", "Stream_Link_4", "Stream_Link_5", "Stream_Link_6", "Organization", "SponsorText", "LastUpdate", "is_inCity", "is_motion"]]
cctv_list_itic = getCamList_iTic()

cctv_list_ubon = process_cctv_names(cctv_list_ubon)
cctv_list_itic = process_cctv_names(cctv_list_itic)

for i in cctv_list_ubon:
    logger.info(i)

for i in cctv_list_itic:
    logger.info(i)


add_camRecord_Ubon(cctv_list_ubon)
add_camRecord_iTic(cctv_list_itic)

all_cctv_ids = retrieve_camID()

offline_cctvs, online_cctvs = detect_cctv_status(all_cctv_ids, cctv_list_ubon, cctv_list_itic)
offline_cctvs = create_cctv_status_dict(offline_cctvs, False)
online_cctvs = create_cctv_status_dict(online_cctvs, True)
update_isCamOnline(offline_cctvs)
update_isCamOnline(online_cctvs)


'''
write python function that do the following:
1. It should accept a list of tuple
2. It should take the second index of all tuple in the list to work with
3. That data is the name of CCTV
4. The issue is that some name also have cctv id include Infront which I don't want. Please use Regx to process it. Here are the rules 
5. Any name that have all character in English are ok
6. Most of the cctv name should start with the Thai character
7. Any name that start with number is ok, but it should follow by space and Thai character.
8. Any name that have parenthesis like this "(จ.หนองบัวลำภู) 210 - อ.เมืองหนองบัวลำภู จ.หนองบัวลำภู ทิศทางมุ่งหน้าเข้า จ.หนองบัวลำภู" should be fix by remove the first part and remain only "อ.เมืองหนองบัวลำภู จ.หนองบัวลำภู ทิศทางมุ่งหน้าเข้า จ.หนองบัวลำภู"
9. But some name will just come with parenthesis like this without number follow at the back "(จ.ฉะเชิงเทรา) หน้าโรงเรียนเทพประสิทธิ์วิทยา" so fix it to be like this "หน้าโรงเรียนเทพประสิทธิ์วิทยา"
10. Any name that come like this "CRM-014 หน้าธนาคารกสิกรไทย สาขาตลาดนาเกลือ กล้องตัวที่ 2" you have to fix to be like this "หน้าธนาคารกสิกรไทย สาขาตลาดนาเกลือ กล้องตัวที่ 2". Please note that "CRM-014" is not a fixed format, it sometime come with more or less english character or more or less number behine dash
11. 
12. This prefixes "ATC4-03" still exist
13. Please note that "CRM-014" is not a fixed format, it sometime come with more or less english character or more or less number behind dash
14. Please note that "(จ.หนองบัวลำภู) 210 - " is not a fixed format, it sometime come with more or less number before dash
'''