import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation, useSearchParams } from "react-router-dom";



import {
    Form, Stack, FormGroup, Button, NumberInput, FileUploader, Callout, Loading, Accordion, AccordionItem, ContainedList, ContainedListItem, CheckboxGroup, Checkbox
} from "@carbon/react";

function Datasets() {
    const BE_URL = process.env.REACT_APP_API_URL;

    const navigate = useNavigate();
    const location = useLocation();

    // If your route is /project/:project_id
    const [searchParams] = useSearchParams();
    const projectId = searchParams.get("project_id"); // Access ?file=yourfilename.pdf

    const [datasets, setDatasets] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);


    // form state
    const [selectedFile, setSelectedFile] = useState(null);
    const [nPast, setNPast] = useState(2);
    const [n1Next, setN1Next] = useState(2);
    const [n2Next, setN2Next] = useState(2);

    async function getDatasets() {

        const res = await fetch(`${BE_URL}/get_datasets_by_projectid?project_id=${projectId}`);
        console.log("length: " + res.length)
        if (!res.ok) throw new Error("Failed to fetch datasets");

        return await res.json();
    }

    function updateColumnFlag(dataset_id, column_name, flagName, checked) {
        setDatasets((prev) =>
            prev.map((ds) =>
                ds.dataset_id !== dataset_id
                    ? ds
                    : {
                        ...ds,
                        columns: ds.columns.map((col) =>
                            col.column_name !== column_name
                                ? col
                                : { ...col, [flagName]: checked ? "Y" : "N" }
                        ),
                    }
            )
        );
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

    useEffect(() => {
        getDatasets()
            .then((data) => setDatasets(normalizeDatasets(data)))
            .catch((err) => setError(err.message));
    }, [projectId]);

    const handleSubmit = async (e) => {

        e.preventDefault();
        setError(null);

        if (!projectId) {
            setError("Missing project_id from URL.");
            return;
        }
        if (!selectedFile) {
            setError("Please select a file.");
            return;
        }

        console.log("selectedFile:", selectedFile);
        console.log("selectedFile size:", selectedFile?.size);

        const formData = new FormData();
        formData.append("file", selectedFile); // must match FastAPI param name: file
        formData.append("project_id", projectId);
        formData.append("n_past_week_for_training", String(nPast));
        formData.append("n1_next_week_for_prediction", String(n1Next));
        formData.append("n2_next_week_for_prediction", String(n2Next));

        try {
            setLoading(true);

            // Use axios for multipart; do NOT manually set Content-Type with boundary
            await axios.post(`${BE_URL}/create_dataset`, formData);

            // refresh list after success
            window.location.reload();


        } catch (err) {
            setError(err?.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    };

    async function updateDataset(dataset) {
        const payload = {
            project_id: dataset.project_id,
            dataset_id: dataset.dataset_id,
            columns: dataset.columns.map(col => ({
                column_name: col.column_name,
                is_forecast_key: col.is_forecast_key,
                is_target: col.is_target,
                is_date: col.is_date,
                is_feature: col.is_feature,
            })),
        };

        setLoading(true);

        await axios.post(
            `${process.env.REACT_APP_API_URL}/update_dataset`,
            payload,
            {
            headers: {
                "Content-Type": "application/json",
            },
            }
        );

        setLoading(false);
    }

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>CREATE NEW DATASET</h3>

                    {error && (
                        <Callout kind="error" title="Error">
                            {error}
                        </Callout>
                    )}

                    <Form onSubmit={handleSubmit}>
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

                                <NumberInput
                                    id="n1"
                                    label="Forecasting Horizon (in week)"
                                    min={1}
                                    max={100}
                                    value={n1Next}
                                    step={1}
                                    onChange={(evt, { value }) => setN1Next(Number(value))}
                                />

                                <NumberInput
                                    id="n2"
                                    label="Maximum Forecasting Horizon for Classification (in week)"
                                    min={1}
                                    max={100}
                                    value={n2Next}
                                    step={1}
                                    onChange={(evt, { value }) => setN2Next(Number(value))}
                                />

                                <NumberInput
                                    id="npast"
                                    label="Training Horizon (in week)"
                                    min={1}
                                    max={100}
                                    value={nPast}
                                    step={1}
                                    onChange={(evt, { value }) => setNPast(Number(value))}
                                />
                            </FormGroup>

                            <Button type="button" disabled={loading} onClick={handleSubmit}>
                                {loading ? "Uploading..." : "Submit"}
                            </Button>
                        </Stack>
                    </Form>
                </div>

                <div className='form-group'>

                    <h3>LIST OF DATASETS</h3>

                    {datasets.map((ds, i) => (
                        <Accordion>
                            <AccordionItem title={ds.table_path}>
                                <p>Dataset ID: {ds.dataset_id}</p>
                                <p>Training Horizon (in weeks): {ds.n_past_week_for_training}</p>
                                <p>Forecasting Horizon (in weeks): {ds.n1_next_week_for_prediction}</p>
                                <p>Maximum Forecasting Horizon (in weeks): {ds.n2_next_week_for_prediction}</p>

                                <ContainedList label="Columns">
                                    {ds.columns.map((col, i) => <ContainedListItem key={i}>
                                        <div style={{
                                            display: 'grid',
                                            gridTemplateColumns: 'repeat(6, 1fr)',
                                            columnGap: '0.5rem'
                                        }}>
                                            <span>{col.column_name}</span>
                                            <span>{col.column_type}</span>
                                            <span>
                                                <Checkbox
                                                    id={`key-${ds.dataset_id}-${col.column_name}`}
                                                    labelText="Key"
                                                    checked={col.is_forecast_key === "Y"}
                                                    onChange={(e, data) => {
                                                        updateColumnFlag(ds.dataset_id, col.column_name, "is_forecast_key", data.checked)
                                                    }}
                                                />
                                            </span>
                                            <span>
                                                <Checkbox
                                                    id={`target-${ds.dataset_id}-${col.column_name}`}
                                                    labelText="Target"
                                                    checked={col.is_target === "Y"}
                                                    onChange={(e, data) => {
                                                        updateColumnFlag(ds.dataset_id, col.column_name, "is_target", data.checked)
                                                    }}
                                                />
                                            </span>
                                            <span>
                                                <Checkbox
                                                    id={`date-${ds.dataset_id}-${col.column_name}`}
                                                    labelText="Date"
                                                    checked={col.is_date === "Y"}
                                                    onChange={(e, data) => {
                                                        updateColumnFlag(ds.dataset_id, col.column_name, "is_date", data.checked)
                                                    }}
                                                />
                                            </span>
                                            <span>
                                                <Checkbox
                                                    id={`feat-${ds.dataset_id}-${col.column_name}`}
                                                    labelText="Feature"
                                                    checked={col.is_feature === "Y"}
                                                    onChange={(e, data) => {
                                                        console.log("checked:", data.checked);
                                                        updateColumnFlag(ds.dataset_id, col.column_name, "is_feature", data.checked)
                                                    }}
                                                />
                                            </span>

                                        </div>
                                    </ContainedListItem>)}
                                </ContainedList>
                                <Button type="primary" disabled={loading} onClick={() => updateDataset(ds)}>
                                    {loading ? "Updating..." : "Update"}
                                </Button>
                            </AccordionItem>
                        </Accordion>
                    ))}



                    {loading == true && (
                        <Loading
                            active
                            className="some-class"
                            description="Loading"
                            withOverlay={loading}
                        />
                    )}


                </div>
            </div>

        </div>

    );
}

export default Datasets;
