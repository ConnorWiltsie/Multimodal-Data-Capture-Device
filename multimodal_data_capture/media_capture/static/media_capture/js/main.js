$(document).ready(function () {
    let isRecording = false;

    $('#startRecording').click(function () {
        if (isRecording) {
            console.log("Already recording, ignoring start request");
            return;
        }
        isRecording = true;
        $.post('/start_recording/', {
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        }, function (data) {
            alert(data.status);
            $('#startRecording').prop('disabled', true);
            $('#stopRecording').prop('disabled', false);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error starting recording:", textStatus, errorThrown);
            alert("Error starting recording: " + errorThrown);
            isRecording = false;
        });
    });

    $('#stopRecording').click(function () {
        if (!isRecording) {
            console.log("Not recording, ignoring stop request");
            return;
        }
        isRecording = false;
        $.post('/stop_recording/', {
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        }, function (data) {
            alert(data.status);
            $('#startRecording').prop('disabled', false);
            $('#stopRecording').prop('disabled', true);
            updatePageContent();
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error stopping recording:", textStatus, errorThrown);
            alert("Error stopping recording: " + errorThrown);
            $('#startRecording').prop('disabled', false);
            $('#stopRecording').prop('disabled', true);
        });
    });

    function updatePageContent() {
        console.log("Updating page content...");
        $.get('/', function (data) {
            console.log("Received updated content");
            var newContent = $(data);
            var newAudioContainer = newContent.find('.audio-container');
            console.log("New audio container content:", newAudioContainer.html());
            $('.audio-container').html(newAudioContainer.html());
            attachTranscribeHandlers();
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error updating page content:", textStatus, errorThrown);
            alert("Error updating page content. Please refresh the page manually.");
        });
    }

    function attachTranscribeHandlers() {
        $('.transcribe-button').off('click').click(function () {
            var audioPath = $(this).data('audio');
            var button = $(this);
            var resultDiv = button.siblings('.transcription-result');

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
    attachTranscribeHandlers();

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
});
