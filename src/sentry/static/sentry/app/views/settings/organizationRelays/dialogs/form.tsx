import React from 'react';
import styled from '@emotion/styled';

import {t} from 'app/locale';
import QuestionTooltip from 'app/components/questionTooltip';
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
    <React.Fragment>
      <Field
        flexibleControlStateSize
        label={t('Display Name')}
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
        label={
          <Label>
            <div>{t('Relay Key')}</div>
            <QuestionTooltip
              position="top"
              size="sm"
              title={t(
                'Only enter the Relay Key value from your credentials file. Never share the Secret key with Sentry or any third party'
              )}
            />
          </Label>
        }
        error={errors.publicKey}
        inline={false}
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
      <Field flexibleControlStateSize label={t('Description')} inline={false} stacked>
        <Textarea
          name="description"
          onChange={handleChange('description')}
          value={values.description}
          disabled={disables.description}
        />
      </Field>
    </React.Fragment>
  );
};

export default Form;

const TextField = styled(Input)`
  font-size: ${p => p.theme.fontSizeSmall};
  margin-bottom: 0;
  height: 40px;
  input {
    height: 40px;
  }
`;

const Label = styled('div')`
  display: grid;
  grid-gap: ${space(1)};
  grid-template-columns: max-content max-content;
  align-items: center;
`;
