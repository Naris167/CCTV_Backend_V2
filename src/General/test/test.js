var player = null;
var map = null;
var markers = [];
var currentStreamId = null;
var currentIcon = null;
var defaultIcon = null;

$(document).ready(() => {
    player = videojs('player', {autoplay: 'muted', controls: true});
    const cctvSelect = jQuery('#cctvSelect').on('change', (e) => {
        const streamId = jQuery(e.target).find('option:selected').val();
        openStream(streamId);
    });
    const cctvblank = jQuery('<option></option>').appendTo(cctvSelect).html('-- กรุณาเลือก --');

    for (let i = 0; i < cctvList.length; i++) {
        const cctv = cctvList[i];
        cctv.marker = null;
        const cctvOption = jQuery('<option></option>')
            .appendTo(cctvSelect)
            .attr('value', cctv.streamId)
            .html(cctv.name  + ' (' + cctv.streamId + ')');
    }
});

function openStream(streamId) {
    if (streamId) {
        let oldMarker = markers.find(e => e.streamId == currentStreamId);
        if (oldMarker !== undefined) {
            oldMarker.marker.setIcon(defaultIcon);
        }
        currentStreamId = streamId;
        let newMarker = markers.find(e => e.streamId == streamId);
        if (newMarker !== undefined) {
            map.setCenter(newMarker.marker.getPosition());
            map.setZoom(16);
            newMarker.marker.setIcon(currentIcon);
        }
        player.src({
            src: window.location.protocol + '//'
                + (window.location.hostname == '192.168.200.5' ? '192.168.200.10' : window.location.hostname)
                + ':1935/livecctv/' + streamId + '.stream/playlist.m3u8',
            type: 'application/x-mpegURL',
            //withCredentials: true
        });
        player.play();
    } else {
        //player.addClass('d-none');
        player.pause();
    }
}

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 15.2447, lng: 104.8475 },
        zoom: 14,
    });

    currentIcon = {path: "M0 5a2 2 0 0 1 2-2h7.5a2 2 0 0 1 1.983 1.738l3.11-1.382A1 1 0 0 1 16 4.269v7.462a1 1 0 0 1-1.406.913l-3.111-1.382A2 2 0 0 1 9.5 13H2a2 2 0 0 1-2-2V5zm11.5 5.175l3.5 1.556V4.269l-3.5 1.556v4.35zM2 4a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h7.5a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1H2z", scale: 2, strokeColor: '#ff3333', strokeWeight: 2, fillColor: '#ff3333', fillOpacity: 1};
    defaultIcon = {path: "M0 5a2 2 0 0 1 2-2h7.5a2 2 0 0 1 1.983 1.738l3.11-1.382A1 1 0 0 1 16 4.269v7.462a1 1 0 0 1-1.406.913l-3.111-1.382A2 2 0 0 1 9.5 13H2a2 2 0 0 1-2-2V5zm11.5 5.175l3.5 1.556V4.269l-3.5 1.556v4.35zM2 4a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h7.5a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1H2z", scale: 1, strokeColor: '#999999', strokeWeight: 2, fillColor: '#999999', fillOpacity: 0.5};

    for (let i = 0; i < cctvList.length; i++) {
        const cctv = cctvList[i];
        if (cctv.lat !== null && cctv.lng !== null) {
            let marker = new google.maps.Marker({
                position: { lat: parseFloat(cctv.lat), lng: parseFloat(cctv.lng) },
                map: map,
                icon: defaultIcon,
                title: cctv.name  + ' (' + cctv.streamId + ')',
            });
            marker.addListener('click', () => {
                jQuery('#cctvSelect option[value=' + cctv.streamId + ']').prop('selected', true);
                openStream(cctv.streamId);
            })
            markers.push({streamId : cctv.streamId, marker : marker});
        }
    }
}