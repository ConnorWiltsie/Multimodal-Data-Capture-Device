$(document).ready(function () {
    let isRecording = false;
    let recordingInterval;

    $('#viewAllImages').click(function () {
        console.log("View All Images button clicked");
        $.get('/get_all_images/', function (data) {
            showModal('All Images', data.html);
        }).fail(function (jqXHR, textStatus, errorThrown) {
            console.error("Error getting all images:", textStatus, errorThrown);
            alert("Error getting all images: " + errorThrown);
        });
    });

    $('#viewAllRecordings').click(function () {
        console.log("View All Recordings button clicked");
        $.get('/get_all_recordings/', function (data) {
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
        attachDeleteHandlers();

        if (title === 'All Images') {
            $('#generatePdfButton').click(function () {
                var imagePaths = [];
                $('.image-item img').each(function () {
                    var imgPath = $(this).attr('src');
                    imagePaths.push(imgPath.split('/').pop());
                });

                console.log("Generating PDF with images:", imagePaths);

                $('#pdfStatus').show();

                $.post('/generate_pdf/', {
                    'image_filenames[]': imagePaths,
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                }, function (response, status, xhr) {
                    console.log("PDF generation response:", response);
                    $('#pdfStatus').hide();
                    if (status === 'success') {
                        var blob = new Blob([response], {
                            type: 'application/pdf'
                        });
                        var url = window.URL.createObjectURL(blob);
                        var a = document.createElement('a');
                        a.href = url;
                        a.download = 'all_images.pdf';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                    } else {
                        console.error("Error generating PDF:", xhr.responseText);
                        alert("Error generating PDF: " + xhr.responseText);
                    }
                }).fail(function (jqXHR, textStatus, errorThrown) {
                    console.error("AJAX Error generating PDF:", textStatus, errorThrown);
                    $('#pdfStatus').hide();
                    alert("Error generating PDF.");
                });
            });
        }
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

    function attachDeleteHandlers() {
        $('.delete-button').off('click').click(function () {
            var audioPath = $(this).data('audio');
            console.log("Delete button clicked for audio:", audioPath);

            if (confirm("Are you sure you want to delete this recording and its transcription?")) {
                $.post('/delete_audio/', {
                    'audio_filename': audioPath.split('/').pop(),
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                }, function (data) {
                    console.log("Delete audio response:", data);
                    if (data.status === 'success') {
                        $(this).closest('.audio-item').remove();
                    } else {
                        alert("Error deleting audio: " + data.message);
                    }
                }.bind(this)).fail(function (jqXHR, textStatus, errorThrown) {
                    console.error("AJAX Error deleting audio:", textStatus, errorThrown);
                    alert("Error deleting audio.");
                });
            }
        });

        $('.delete-image').off('click').click(function () {
            var imagePath = $(this).data('image');
            console.log("Delete button clicked for image:", imagePath);

            if (confirm("Are you sure you want to delete this image?")) {
                $.post('/delete_image/', {
                    'image_filename': imagePath.split('/').pop(),
                    'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                }, function (data) {
                    console.log("Delete image response:", data);
                    if (data.status === 'success') {
                        $(this).closest('.image-item').remove();
                    } else {
                        alert("Error deleting image: " + data.message);
                    }
                }.bind(this)).fail(function (jqXHR, textStatus, errorThrown) {
                    console.error("AJAX Error deleting image:", textStatus, errorThrown);
                    alert("Error deleting image.");
                });
            }
        });
    }

    $(document).on('click', '.email-button', function () {
        var fileType = $(this).data('file-type');
        var filePath = $(this).data('file-path');
        var emailAddress = prompt("Please enter your email address:");

        if (emailAddress) {
            $('#emailStatus').show();

            $.post('/email_file/', {
                'file_type': fileType,
                'file_path': filePath,
                'email_address': emailAddress,
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            }, function (data) {
                $('#emailStatus').hide();
                if (data.status === 'success') {
                    alert("Email sent successfully!");
                } else {
                    alert("Error sending email: " + data.message);
                }
            }).fail(function (jqXHR, textStatus, errorThrown) {
                $('#emailStatus').hide();
                console.error("Error sending email:", textStatus, errorThrown);
                alert("Error sending email.");
            });
        }
    });

    attachTranscribeHandlers();
    attachDeleteHandlers();
});
