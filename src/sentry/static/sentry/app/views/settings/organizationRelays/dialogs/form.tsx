import React from 'react';
import styled from '@emotion/styled';

import {t} from 'app/locale';
import Input from 'app/views/settings/components/forms/controls/input';
import Textarea from 'app/views/settings/components/forms/controls/textarea';
import Field from 'app/views/settings/components/forms/field';
import space from 'app/styles/space';

type FormField = 'name' | 'description' | 'publicKey';
type Values = Record<FormField, string>;

type Props = {
  values: Values;
  errors: Partial<Values>;
  disables: Partial<Record<FormField, boolean>>;
  onValidate: (field: FormField) => () => void;
  onChange: (field: FormField, value: string) => void;
};

const Form = ({values, onChange, errors, onValidate, disables}: Props) => {
  const handleChange = (field: FormField) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    onChange(field, event.target.value);
  };

  return (
    <Wrapper>
      <Field
        flexibleControlStateSize
        label={t('Name')}
        error={errors.name}
        inline={false}
        stacked
      >
        <TextField
          type="text"
          name="name"
          onChange={handleChange('name')}
          value={values.name}
          onBlur={onValidate('name')}
          disabled={disables.name}
        />
      </Field>
      <Field
        flexibleControlStateSize
        label={t('Public Key')}
        error={errors.publicKey}
        inline={false}
        help={t(
          'Only enter the public_key value from your credentials file. Never share the secret_key with Sentry or any third party'
        )}
        stacked
      >
        <TextField
          type="text"
          name="publicKey"
          onChange={handleChange('publicKey')}
          value={values.publicKey}
          onBlur={onValidate('publicKey')}
          disabled={disables.publicKey}
        />
      </Field>
      <Field
        flexibleControlStateSize
        label={t('Description')}
        error={errors.description}
        inline={false}
        stacked
      >
        <Textarea
          name="description"
          onChange={handleChange('description')}
          value={values.description}
          onBlur={onValidate('description')}
          disabled={disables.description}
        />
      </Field>
    </Wrapper>
  );
};

export default Form;

const TextField = styled(Input)`
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
