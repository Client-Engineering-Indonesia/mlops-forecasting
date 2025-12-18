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
    Notification
} from '@carbon/icons-react';


import './Predictions.css'


import { useNavigate } from 'react-router-dom';
import axios from 'axios';


function Predictions() {

    const BE_URL = process.env.REACT_APP_API_URL;
    //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>CREATE NEW PREDICTION</h3>

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
                                <div>
                                    <Select
                                        id="select-1"
                                        labelText="Select a model"
                                        size="md"
                                    >
                                        <SelectItem
                                            text=""
                                            value=""
                                        />
                                        <SelectItem
                                            text="An example option that is really long to show what should be done to handle long text"
                                            value="An example option that is really long to show what should be done to handle long text"
                                        />
                                        <SelectItem
                                            text="Option 2"
                                            value="option-2"
                                        />
                                        <SelectItem
                                            text="Option 3"
                                            value="option-3"
                                        />
                                        <SelectItem
                                            text="Option 4"
                                            value="option-4"
                                        />
                                    </Select>
                                </div>
                            </FormGroup>

                            <Button type="submit" className="some-class">
                                Submit
                            </Button>

                        </Stack>

                    </Form>
                </div>

                <div className='form-group'>

                    <h3>LIST OF PREDICTIONS</h3>



                    <Accordion>
                        <AccordionItem title="Prediction 1">

                            <p>
                                <b>Processed At</b>: 2025-01-01 10:00:00
                            </p>

                            <p>
                                <Button type="submit" className="some-class">
                                    Download Prediction
                                </Button>
                            </p>
                        </AccordionItem>
                    </Accordion>


                </div>
            </div>

        </div>
    );
}

export default Predictions;