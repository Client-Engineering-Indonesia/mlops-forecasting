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


import './Features.css'



function Features() {

    const BE_URL = process.env.REACT_APP_API_URL;
    const BE_URL2 = process.env.REACT_APP_API_URL2;
    //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

    // If your route is /project/:project_id
    const [searchParams] = useSearchParams();
    const projectId = searchParams.get("project_id"); // Access ?file=yourfilename.pdf

    const [datasets, setDatasets] = useState([]);
    const [features, setFeatures] = useState([]);
    const [error, setError] = useState(null);

    const [selectedDataset, setSelectedDataset] = useState("");

    const [loading, setLoading] = useState(false);

    async function getDatasets() {

        setLoading(true);

        const res = await fetch(`${BE_URL}/get_datasets_by_projectid?project_id=${projectId}`);
        console.log("length: " + res.length)
        if (!res.ok) throw new Error("Failed to fetch datasets");

        setLoading(false);

        return await res.json();
    }

    const normalizeFlag = (v) => (v === "Y" ? "Y" : "N");

    const normalizeDatasets = (data) =>
        data.map((ds) => ({
            ...ds,
            columns: ds.columns.map((c) => ({
                ...c,
                is_forecast_key: normalizeFlag(c.is_forecast_key),
                is_target: normalizeFlag(c.is_target),
                is_date: normalizeFlag(c.is_date),
                is_feature: normalizeFlag(c.is_feature),
            })),
        }));

    async function createBasicFeatureStore() {
        
        const payload = {
            dataset_id: selectedDataset,
        };

        console.log(payload)

        setLoading(true);

        await axios.post(
            `${process.env.REACT_APP_API_URL2}/create_basic_feature_store`,
            payload,
            {
            headers: {
                "Content-Type": "application/json",
            },
            }
        );

        setLoading(false);
    }

    useEffect(() => {
        getDatasets()
            .then((data) => setDatasets(normalizeDatasets(data)))
            .catch((err) => setError(err.message));
    }, [projectId]);

    async function getFeatures() {

        const res = await fetch(`${BE_URL2}/get_features_by_projectid?project_id=${projectId}`);
        console.log("length: " + res.length)
        if (!res.ok) throw new Error("Failed to fetch datasets");

        return await res.json();
    }

    useEffect(() => {
        getFeatures()
            .then((data) => setFeatures(data))
            .catch((err) => setError(err.message));
    }, [projectId]);

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>CREATE NEW FEATURE SET</h3>

                    <Form >
                        <Stack gap={7}>
                            <FormGroup legendText="Input feature details here">
                                <div>
                                    <Select
                                        id="select-1"
                                        labelText="Select a dataset"
                                        size="md"
                                        onChange={(e) => {
                                            setSelectedDataset(e.target.value);
                                        }}
                                    >
                                        <SelectItem
                                            text=""
                                            value=""
                                        />
                                        {datasets.map((ds, i) => (
                                            <SelectItem
                                                text={ds.base_data_table_path}
                                                value={ds.dataset_id}
                                            />
                                        ))}
                                        
                                    </Select>
                                </div>
                            </FormGroup>

                            <Button 
                                type="button"
                                className="some-class" 
                                disabled={!selectedDataset || loading}
                                onClick={createBasicFeatureStore}
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

                    <h3>LIST OF FEATURE SETS</h3>

                    {features.map((ds, i) => (
                        <Accordion>
                            <AccordionItem title={ds.table_path}>

                                <p>Total Features: {ds.total_features}</p>
                                <p>From Dataset: {ds.from_dataset}</p>

                                <ContainedList label="Features">
                                    {ds.features_list.map((col, j) => <ContainedListItem key={j}>
                                        <div style={{
                                            display: 'grid',
                                            gridTemplateColumns: 'repeat(1, 1fr)',
                                            columnGap: '0.5rem'
                                        }}>
                                            <span>{col}</span>
                                            
                                        </div>
                                    </ContainedListItem>)}
                                </ContainedList>
                            </AccordionItem>
                        </Accordion>
                    ))}

                </div>

                
            </div>

        </div>
    );
}

export default Features;