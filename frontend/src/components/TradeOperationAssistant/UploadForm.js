import React, { useState, useEffect } from 'react';
import {
  TextArea,
  Stack,
  Button,
  Form,
  FormGroup,
  TextInput,
  RadioButtonGroup,
  RadioButton,
  Slider,
  Accordion,
  AccordionItem,
  InlineNotification,
  FileUploader,
  Loading,
  ToastNotification
} from '@carbon/react';
import { useCookies } from 'react-cookie';
import { Add, ThumbsUp, ThumbsDown } from '@carbon/icons-react';
import axios from 'axios';

const BE_URL = 'http://127.0.0.1:8443/'

const UploadForm = () => {

    const [isFormSubmitted, setIsFormSubmitted] = useState(false);
    const [fileName, setFileName] = useState('Choose file to upload');
    const [uploadedFiles, setUploadedFiles] = useState(null);
    const [uploadedTime, setUploadedTime] = useState("");
    const [fileLoadingStatus, setFileLoadingStatus] = useState(false);
    const [cosFilename, setCosFilename] = useState("");
    const [cosBucketName, setCosBucketName] = useState("");

    const getFormattedDateTime = () => {
        const now = new Date();

        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, "0");
        const date = String(now.getDate()).padStart(2, "0");
        const hours = String(now.getHours()).padStart(2, "0");
        const minutes = String(now.getMinutes()).padStart(2, "0");
        const seconds = String(now.getSeconds()).padStart(2, "0");

        return `${year}-${month}-${date} ${hours}:${minutes}:${seconds}`;
    };

    const submitApplication = async (event) => {
        event.preventDefault();
        setFileLoadingStatus(true);

        try {

            const formData = new FormData();

            formData.append('file', uploadedFiles);

            const response = await axios.post(BE_URL + 'upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    accept: 'application/json',
                }
            });

            if (response.status === 200) {
                setCosFilename(response.data.object_name);
                setCosBucketName(response.data.nucket_name);
                setIsFormSubmitted(true);
            }
        } catch (error) {
            console.log(error);
        }

        setFileLoadingStatus(false);

    }
  
    return (
      <div className="login-container" style={{width: '100%'}}>

        {isFormSubmitted == true && (
            <div>
                <ToastNotification style={{width: '500px'}}
                aria-label="closes notification"
                caption={getFormattedDateTime()}
                kind="success"
                onClose={() => {}}
                onCloseButtonClick={() => {}}
                role="status"
                statusIconDescription="notification"
                subtitle={"You can use this ID for your next analysis. " + cosFilename}
                timeout={0}
                title="Your file has been successfully uploaded!"
                />
            </div>
        )}

        {fileLoadingStatus == true && (
            <Loading
            active
            className="some-class"
            description="Loading"
            />
        )}

        

        {isFormSubmitted == false && (
            <div>
                <FormGroup style={{maxWidth: '100%'}}>
                    <Stack gap={7}>
                    <h2>Upload Form</h2>

                    <div className="cds--file__container" style={{width: '500px'}}>
                    <FileUploader
                        accept={[
                        '.jpg',
                        '.png',
                        '.pdf'
                        ]}
                        buttonKind="secondary"
                        buttonLabel="Add file"
                        filenameStatus="edit"
                        iconDescription="Delete file"
                        labelDescription="Max file size is 10 MB. Only .jpg, .pdf files are supported."
                        labelTitle="Upload files"
                        name=""
                        onChange={
                            async (event) => {
                                const file = event.target.files[0];
                                setUploadedFiles(file);
                            }
                        }
                        onClick={() => {}}
                        onDelete={() => {}}
                        size="md"
                    />
                    </div>

                    <Button onClick={submitApplication} style={{marginBottom: '1rem'}}>
                    Upload
                    </Button>
                    </Stack>
                    
                </FormGroup>
            </div>
        )}
      
      </div>
    );
  }
  
  export default UploadForm;

