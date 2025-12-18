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
import React, { useState, useEffect } from 'react';
import {
    Add,
    View,
    AiLaunch,
    TrashCan,
    Notification
} from '@carbon/icons-react';


import './Models.css'


import { useNavigate } from 'react-router-dom';
import axios from 'axios';


function Models() {

    const BE_URL = process.env.REACT_APP_API_URL;
    //console.log("BE_URL: " + BE_URL); // should print http://localhost:8000

    return (
        <div className="sub-main-page">
            <div className="overview" style={{ display: 'flex', justifyContent: 'center' }}>

                <div className='form-group'>

                    <h3>CREATE NEW MODEL</h3>

                    <Form>
                        <Stack gap={7}>
                            <FormGroup legendText="Input model details here">
                                <div>
                                    <Select
                                        id="select-1"
                                        labelText="Select a feature set"
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

                    <h3>LIST OF MODELS</h3>



                    <Accordion>
                        <AccordionItem title="Model 1">

                            <p>
                                <b>Algorithm</b>: XGB
                            </p>
                            <p>
                                <b>Testing Evaluation</b>: Precision (0.94) Recall (0.89) AUC (0.87) Accuracy (0.99)
                            </p>
                            <p>
                                <b>Out of Time Evaluation</b>: Precision (0.94) Recall (0.89) AUC (0.87) Accuracy (0.99)
                            </p>
                            <p>
                                <Button type="submit" className="some-class">
                                    Download OOT Evaluation
                                </Button>
                            </p>


                        </AccordionItem>

                        <AccordionItem title="Model 2">

                            <p>
                                <b>Algorithm</b>: XGB
                            </p>
                            <p>
                                <b>Testing Evaluation</b>: Precision (0.94) Recall (0.89) AUC (0.87) Accuracy (0.99)
                            </p>
                            <p>
                                <b>Out of Time Evaluation</b>: 
                            </p>
                            <p>
                                <Button type="submit" className="some-class">
                                    Upload OOT
                                </Button>
                            </p>


                        </AccordionItem>
                    </Accordion>


                </div>
            </div>

        </div>
    );
}

export default Models;