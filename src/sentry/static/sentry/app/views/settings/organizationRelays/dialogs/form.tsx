import React from 'react';
import styled from '@emotion/styled';

import {t} from 'app/locale';
import TextField from 'app/components/forms/textField';
import TextareaField from 'app/components/forms/textareaField';
import space from 'app/styles/space';

import FormField from './formField';

type FormField = 'name' | 'description' | 'publicKey';
type Values = Record<FormField, string>;

type Props = {
  values: Values;
  errors: Partial<Values>;
  disables: Partial<Record<FormField, boolean>>;
  onValidate: (field: FormField) => () => void;
  onChange: (field: FormField, value: string) => void;
};

const Form = ({values, errors, onValidate, onChange, disables}: Props) => (
  <Wrapper>
    <FormField label={t('Name')} isFullWidth>
      <StyledTextField
        name="name"
        onChange={(value: string) => {
          onChange('name', value);
        }}
        value={values.name}
        onBlur={onValidate('name')}
        error={errors.name}
        disabled={disables.name}
      />
    </FormField>
    <FormField label={t('Key')} isFullWidth>
      <TextareaField
        name="publicKey"
        onChange={value => {
          onChange('publicKey', value as string);
        }}
        value={values.publicKey}
        onBlur={onValidate('publicKey')}
        error={errors.publicKey}
        disabled={disables.publicKey}
      />
    </FormField>
    <FormField label={t('Description')} isFullWidth>
      <TextareaField
        name="description"
        onChange={value => {
          onChange('description', value as string);
        }}
        value={values.description}
        onBlur={onValidate('description')}
        error={errors.description}
        disabled={disables.description}
      />
    </FormField>
  </Wrapper>
);

export default Form;

const StyledTextField = styled(TextField)`
  font-size: ${p => p.theme.fontSizeSmall};
  height: 40px;
  input {
    height: 40px;
  }
`;

const Wrapper = styled('div')`
  display: grid;
  grid-gap: ${space(1)};
`;
