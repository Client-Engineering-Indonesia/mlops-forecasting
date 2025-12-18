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
    Notification
} from '@carbon/icons-react';


import './Datasets.css'


import { useNavigate } from 'react-router-dom';
import axios from 'axios';


function Datasets() {

    const BE_URL = process.env.REACT_APP_API_URL;
    //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>CREATE NEW DATASET</h3>

                    <Form>
                        <Stack gap={7}>
                            <FormGroup legendText="Input dataset details here">
                                <div className="cds--file__container">
                                    <FileUploader
                                        accept={[
                                            '.csv',
                                            '.png'
                                        ]}
                                        buttonKind="primary"
                                        buttonLabel="Add file"
                                        filenameStatus="edit"
                                        iconDescription="Delete file"
                                        labelDescription="Max file size is 1 MB. Only .csv is supported."
                                        maxFileSize={1048576}
                                        multiple
                                        name=""
                                        onChange={function c_e() { }}
                                        onClick={function c_e() { }}
                                        onDelete={function c_e() { }}
                                        size="md"
                                    />
                                </div>
                                <NumberInput className="some-class" id="number-input-1" label="Forecasting Horizon (in week)" min={1} max={100} value={2} step={1} iconDescription="Add/decrement number" />
                                <NumberInput className="some-class" id="number-input-1" label="Training Horizon (in week)" min={1} max={100} value={2} step={1} iconDescription="Add/decrement number" />
                            </FormGroup>

                            <Button type="submit" className="some-class">
                                Submit
                            </Button>

                        </Stack>

                    </Form>
                </div>

                <div className='form-group'>

                    <h3>LIST OF DATASETS</h3>



                    <Accordion>
                        <AccordionItem title="Dataset 1">

                            <p>
                                <b>Filepath</b>: /dataset.csv
                            </p>
                            <p>
                                <b>Forecasting Horizon</b>: 1 week(s)
                            </p>
                            <p>
                                <b>Training Horizon</b>: 2 week(s)
                            </p>
                            <p>
                                <b>Number of columns</b>: 10
                            </p>
                            <p>
                                <b>Uploaded At</b>: 2025-01-01 10:00:00
                            </p>

                            <ContainedList label="Columns">
                                {[...Array(4)].map((_, i) => <ContainedListItem key={i}>
                                    <div style={{
                                        display: 'grid',
                                        gridTemplateColumns: 'repeat(5, 1fr)',
                                        columnGap: '1rem'
                                    }}>
                                        <span>Column Name</span>
                                        <span>Column Description</span>
                                        <span><CheckboxGroup
                                            className="some-class"
                                            invalidText="Invalid message goes here"
                                            warnText="Warning message goes here"
                                        >
                                            <Checkbox
                                                id={`checkbox-label-${i}`}
                                                labelText="Used for feature"
                                            />
                                        </CheckboxGroup></span>
                                        <span><CheckboxGroup
                                            className="some-class"
                                            invalidText="Invalid message goes here"
                                            warnText="Warning message goes here"
                                        >
                                            <Checkbox
                                                id={`target-label-${i}`}
                                                labelText="Used for target"
                                            />
                                        </CheckboxGroup></span>
                                        <span><CheckboxGroup
                                            className="some-class"
                                            invalidText="Invalid message goes here"
                                            warnText="Warning message goes here"
                                        >
                                            <Checkbox
                                                id={`date-label-${i}`}
                                                labelText="Used for date"
                                            />
                                        </CheckboxGroup></span>
                                    </div>
                                </ContainedListItem>)}
                            </ContainedList>




                        </AccordionItem>
                    </Accordion>


                </div>
            </div>

        </div>
    );
}

export default Datasets;