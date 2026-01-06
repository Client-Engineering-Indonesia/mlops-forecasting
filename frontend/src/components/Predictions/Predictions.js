import {
    Accordion,
    AccordionItem,
    Breadcrumb,
    TextInput,
    TextArea,
    Select,
    SelectItem,
    Form,
    Stack,
    FormGroup,
    ContainedList,
    ContainedListItem,
    CheckboxGroup,
    Checkbox,
    NumberInput,
    FileUploader,
    BreadcrumbItem,
    DataTable,
    Link,
    Table,
    TableHead,
    TableRow,
    TableHeader,
    TableBody,
    TableCell,
    TableToolbar,
    TableContainer,
    TableToolbarSearch,
    Dropdown,
    Button,
    Callout,
    Loading,
    unstable__IconIndicator as IconIndicator,
} from '@carbon/react';
import React, { useState, useEffect } from 'react';
import {
    Add,
    View,
    AiLaunch,
    TrashCan,
    Notification,
    Model
} from '@carbon/icons-react';


import './Predictions.css'


import { useNavigate, useLocation, useSearchParams } from "react-router-dom";
import axios from 'axios';


function Predictions() {

    const BE_URL = process.env.REACT_APP_API_URL;
    const BE_URL2 = process.env.REACT_APP_API_URL2;
    const BE_URL3= process.env.REACT_APP_API_URL3;

    const [searchParams] = useSearchParams();
    const projectId = searchParams.get("project_id"); // Access ?file=yourfilename.pdf

    const [selectedFile, setSelectedFile] = useState(null);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [models, setModels] = useState([]);
    const [predictions, setPredictions] = useState([]);

    const [selectedModel, setSelectedModel] = useState("");

    //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

    async function getModels() {

        const res = await fetch(`${BE_URL3}/get_models_by_projectid?project_id=${projectId}`);
        console.log("length: " + res.length)
        if (!res.ok) throw new Error("Failed to fetch datasets");

        return await res.json();
    }

    async function getPredictions() {

        const res = await fetch(`${BE_URL3}/get_predictions?project_id=${projectId}`);
        console.log("length: " + res.length)
        if (!res.ok) throw new Error("Failed to fetch datasets");

        return await res.json();
    }
    

    async function getPredictionResult() {

        setLoading(true);

        const formData = new FormData();
        formData.append("file", selectedFile); // must match FastAPI param name: file
        formData.append("model_id", selectedModel);

        try {
            

            // Use axios for multipart; do NOT manually set Content-Type with boundary
            await axios.post(`${BE_URL3}/get_model_prediction`, formData);

            // refresh list after success
            window.location.reload();


        } catch (err) {
            setError(err?.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }

        setLoading(false);

        window.location.reload();
    }

    useEffect(() => {
        async function loadAll() {
            try {
                setLoading(true);

                const [predictionsData, ModelsData] = await Promise.all([
                    getPredictions(),
                    getModels(),
                ]);

                setPredictions(predictionsData);
                setModels(ModelsData);

            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }
        loadAll();
    }, [projectId]);

    const downloadPredictionResult = async (predFilePath) => {
        setLoading(true);
        const res = await fetch(`${BE_URL3}/download_prediction_result?pred_file_path=${encodeURIComponent(predFilePath)}`);

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = predFilePath.split("/").pop();
        a.click();

        window.URL.revokeObjectURL(url);
        setLoading(false);
        
    }

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>GET PREDICTIONS</h3>

                    <Form>
                        <Stack gap={7}>
                            <FormGroup legendText="Input dataset details here">
                                
                                <div className="cds--file__container">
                                                                    <FileUploader
                                                                        accept={[".csv", ".xls", ".xlsx"]}
                                                                        buttonKind="primary"
                                                                        buttonLabel="Add file"
                                                                        filenameStatus="edit"
                                                                        labelDescription="Max file size is 15 MB. Only .csv .xls .xlsx are supported."
                                                                        maxFileSize={20048576}
                                                                        multiple={false}                 // IMPORTANT: backend expects single file
                                                                        onChange={(e) => {
                                                                            const f = e?.target?.files?.[0];
                                                                            setSelectedFile(f || null);
                                                                        }}
                                                                        onDelete={() => setSelectedFile(null)}
                                                                        size="md"
                                                                    />
                                                                </div>
                                <div>
                                    <Select
                                        id="select-1"
                                        labelText="Select a feature store"
                                        size="md"
                                        onChange={(e) => {
                                            setSelectedModel(e.target.value);
                                        }}
                                    >
                                        <SelectItem
                                            text=""
                                            value=""
                                        />
                                        {models.map((ds, i) => (
                                            <SelectItem
                                                text={ds.model_id}
                                                value={ds.model_id}
                                            />
                                        ))}
                                        
                                    </Select>
                                </div>
                            </FormGroup>

                            <Button 
                                type="submit" 
                                className="some-class"
                                disabled={!selectedModel || loading}
                                onClick={getPredictionResult}
                            >
                                Submit
                            </Button>

                        </Stack>

                    </Form>
                </div>

                {loading == true && (
                                                                    <Loading
                                                                        active
                                                                        className="some-class"
                                                                        description="Loading"
                                                                        withOverlay={loading}
                                                                    />
                                                                )}

                <div className='form-group'>

                    <h3>LIST OF PREDICTIONS</h3>

                    {predictions.map((ds, i) => (
                        <Accordion>
                            <AccordionItem title={ds.pred_file_path}>

                                <p>Created At: {ds.creation_date}</p>
                                <p>From Model: {ds.model_id}</p>
                                <p>
                                    <Button 
                                        type="button"
                                        kind="secondary"
                                        className="some-class" 
                                        onClick={() => downloadPredictionResult(ds.pred_file_path)}
                                    >
                                        Download Training Result
                                    </Button>
                                </p>

                                
                            </AccordionItem>
                        </Accordion>
                    ))}



                </div>
            </div>

        </div>
    );
}

export default Predictions;