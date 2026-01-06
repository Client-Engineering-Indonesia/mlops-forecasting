import {
    Accordion,
    AccordionItem,
    Breadcrumb,
    TextInput,
    TextArea,
    Form,
    Stack,
    FormGroup,
    ContainedList,
    ContainedListItem,
    CheckboxGroup,
    Checkbox,
    Select,
    SelectItem,
    NumberInput,
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
import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";
import {
    Add,
    View,
    AiLaunch,
    TrashCan,
    Notification
} from '@carbon/icons-react';


import './Models.css'



function Models() {

    const BE_URL = process.env.REACT_APP_API_URL;
    const BE_URL2 = process.env.REACT_APP_API_URL2;
    const BE_URL3= process.env.REACT_APP_API_URL3;
    //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

    // If your route is /project/:project_id
    const [searchParams] = useSearchParams();
    const projectId = searchParams.get("project_id"); // Access ?file=yourfilename.pdf

    const [featureStores, setFeatureStores] = useState([]);
    const [models, setModels] = useState([]);
    const [error, setError] = useState(null);

    const [selectedFeatureStore, setSelectedFeatureStore] = useState("");

    const [loading, setLoading] = useState(false);

    async function getFeatureStores() {

        setLoading(true);

        const res = await fetch(`${BE_URL3}/get_feature_stores_by_projectid?project_id=${projectId}`);
        console.log("length: " + res.length)
        if (!res.ok) throw new Error("Failed to fetch datasets");

        setLoading(false);

        return await res.json();
    }

    const downloadTrainingResult = async (modelId) => {
        setLoading(true);
        const res = await fetch(`${BE_URL3}/download_training_result?model_id=${modelId}`);

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = modelId.split("/").pop();
        a.click();

        window.URL.revokeObjectURL(url);
        setLoading(false);
        
    }


    async function createModel() {
        
        const payload = {
            feature_store_id: selectedFeatureStore,
        };

        console.log(payload)

        setLoading(true);

        await axios.post(
            `${process.env.REACT_APP_API_URL3}/create_model`,
            payload,
            {
            headers: {
                "Content-Type": "application/json",
            },
            }
        );

        setLoading(false);

        window.location.reload();
    }


    async function getModels() {

        const res = await fetch(`${BE_URL3}/get_models_by_projectid?project_id=${projectId}`);
        console.log("length: " + res.length)
        if (!res.ok) throw new Error("Failed to fetch datasets");

        return await res.json();
    }

    useEffect(() => {
        async function loadAll() {
            try {
                setLoading(true);

                const [featuresData, ModelsData] = await Promise.all([
                    getFeatureStores(),
                    getModels(),
                ]);

                setFeatureStores(featuresData);
                setModels(ModelsData);

            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        }
        loadAll();
    }, [projectId]);

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>CREATE NEW MODEL</h3>

                    <Form >
                        <Stack gap={7}>
                            <FormGroup legendText="Input feature details here">
                                <div>
                                    <Select
                                        id="select-1"
                                        labelText="Select a feature store"
                                        size="md"
                                        onChange={(e) => {
                                            setSelectedFeatureStore(e.target.value);
                                        }}
                                    >
                                        <SelectItem
                                            text=""
                                            value=""
                                        />
                                        {featureStores.map((ds, i) => (
                                            <SelectItem
                                                text={ds.table_path}
                                                value={ds.feature_store_id}
                                            />
                                        ))}
                                        
                                    </Select>
                                </div>
                            </FormGroup>

                            <Button 
                                type="button"
                                className="some-class" 
                                disabled={!selectedFeatureStore || loading}
                                onClick={createModel}
                            >
                                Submit
                            </Button>

                            {loading == true && (
                                                    <Loading
                                                        active
                                                        className="some-class"
                                                        description="Loading"
                                                        withOverlay={loading}
                                                    />
                                                )}

                        </Stack>

                    </Form>
                </div>

                <div className='form-group'>

                    <h3>LIST OF MODELS</h3>

                    {models.map((ds, i) => (
                        <Accordion>
                            <AccordionItem title={ds.model_id}>

                                <p>Algorithm Used: {ds.alhorithm_used}</p>
                                <p>Training Evaluation: RMSE-{ds.training_evaluation.rmse}</p>
                                <p>Testing Evaluation: RMSE-{ds.testing_evaluation.rmse}</p>
                                <p>From Feature Store: {ds.table_path}</p>
                                <p>
                                    <Button 
                                        type="button"
                                        kind="secondary"
                                        className="some-class" 
                                        onClick={() => downloadTrainingResult(ds.model_id)}
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

export default Models;