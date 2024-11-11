$(document).ready(function () {
    let isRecording = false;
    let recordingInterval;

    $('#viewAllImages').click(function() {
        console.log("View All Images button clicked");
        $.get('/get_all_images/', function(data) {
            showModal('All Images', data.html);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error getting all images:", textStatus, errorThrown);
            alert("Error getting all images: " + errorThrown);
        });
    });

    $('#viewAllRecordings').click(function() {
        console.log("View All Recordings button clicked");
        $.get('/get_all_recordings/', function(data) {
            showModal('All Recordings', data.html);
            attachTranscribeHandlers(); 
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error getting all recordings:", textStatus, errorThrown);
            alert("Error getting all recordings: " + errorThrown);
        });
    });

    $('#recordAudio').click(function () {
        $('#recordingModal').show(); 
    });

   
    $('#closeRecordingModal').click(function () {
        $('#recordingModal').hide(); 
        stopRecording(); 
    });


    $('#startRecordingButton').click(function () {
        console.log("Start Recording button clicked");
        if (isRecording) return;
        isRecording = true;
        $('#startRecordingButton').prop('disabled', true);
        $('#stopRecordingButton').prop('disabled', false);

        let seconds = 0;
        recordingInterval = setInterval(function () {
            seconds++;
            let minutes = Math.floor(seconds / 60);
            let displaySeconds = seconds % 60;
            $('#timer').text(`${String(minutes).padStart(2, '0')}:${String(displaySeconds).padStart(2, '0')}`);
        }, 1000);

        $.post('/start_recording/', {
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error starting recording:", textStatus, errorThrown);
            alert("Error starting recording");
            stopRecording();
        });
    });

    $('#stopRecordingButton').click(function () {
        console.log("Stop Recording button clicked");
        if (!isRecording) return;
        stopRecording();
    });

    function stopRecording() {
        isRecording = false;
        clearInterval(recordingInterval);
        $('#startRecordingButton').prop('disabled', false);
        $('#stopRecordingButton').prop('disabled', true);

        $.post('/stop_recording/', {
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        }, function (data) {
            $('#recordingModal').hide(); 
            $('#timer').text('00:00');

            updatePageContent();

        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error stopping recording:", textStatus, errorThrown);
        });
    }

    $('.close').click(function () {
        $('#modal').hide();
    });

    $(window).click(function (event) {
        if (event.target == $('#modal')[0]) {
            $('#modal').hide();
        }
    });

    function updatePageContent() {
        console.log("Updating page content...");
        $.get('/', function (data) {
            console.log("Received updated content");
            var newContent = $(data);
            var newAudioContainer = newContent.find('.recordings-container');
            var newImagesContainer = newContent.find('.images-container');
            $('.recordings-container').html(newAudioContainer.html());
            $('.images-container').html(newImagesContainer.html());
            attachTranscribeHandlers(); 
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error updating page content:", textStatus, errorThrown);
            alert("Error updating page content. Please refresh the page manually.");
        });
    }

    function updateRecentImages() {
        $.get('/get_recent_images/', function (data) {
            $('.images-container').html(data.html); 
            attachTranscribeHandlers(); 
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error updating recent images:", textStatus, errorThrown);
            alert("Error updating recent images. Please refresh the page manually.");
        });
    }

    function attachTranscribeHandlers() {
        $('.transcribe-button').off('click').click(function () {
            var audioPath = $(this).data('audio');
            var button = $(this);
            var resultDiv = button.siblings('.transcription-result');
            console.log("Transcribe button clicked for:", audioPath); 
            $.post('/start_transcription/', {
                'audio_filename': audioPath.split('/').pop(),
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            }, function (data) {
                button.prop('disabled', true);
                button.text('Transcribing...');
                checkTranscriptionStatus(audioPath, button, resultDiv);
            }).fail(function (jqXHR, textStatus, errorThrown) {
                console.error("Error starting transcription:", textStatus, errorThrown);
                button.text('Transcription Error');
                resultDiv.find('.transcription-text').text('Error: Failed to start transcription');
                resultDiv.show();
            });
        });
    }

    function checkTranscriptionStatus(audioPath, button, resultDiv) {
        $.get('/get_transcription/', {
            'audio_filename': audioPath.split('/').pop()
        }, function (data) {
            if (data.status === 'completed') {
                button.text('Transcription Complete');
                resultDiv.find('.transcription-text').text(data.transcription);
                var downloadLink = resultDiv.find('.download-transcription');
                downloadLink.attr('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(data.transcription));
                downloadLink.show();
                resultDiv.show();
            } else if (data.status === 'error') {
                button.text('Transcription Error');
                resultDiv.find('.transcription-text').text('Error: ' + data.message);
                resultDiv.show();
            } else {
                setTimeout(function () {
                    checkTranscriptionStatus(audioPath, button, resultDiv);
                }, 5000);
            }
        }).fail(function () {
            button.text('Transcription Error');
            resultDiv.find('.transcription-text').text('Error: Failed to get transcription status');
            resultDiv.show();
        });
    }

    function showModal(title, content) {
        $('#modal .modal-content h2').text(title);
        $('#modalContent').html(content); 
        $('#modal').show();
        attachTranscribeHandlers();
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function downloadTranscription(filePath) {
        const link = document.createElement('a');
        link.href = filePath; 
        link.download = filePath.split('/').pop(); 
        document.body.appendChild(link); 
        link.click(); 
        document.body.removeChild(link); 
    }

    const csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    attachTranscribeHandlers();
});